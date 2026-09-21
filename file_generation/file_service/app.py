import base64, io, os, csv, json, zipfile, subprocess, shutil
from pathlib import Path
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from docx import Document
from openpyxl import Workbook
from pptx import Presentation
from fpdf import FPDF, XPos, YPos
import matplotlib.pyplot as plt
import pandas as pd
import magic
import pytesseract
from PIL import Image
from pypdf import PdfReader

app=FastAPI(title='I3S File Generator',version='1.0')
ROOT=Path('/data/files'); ROOT.mkdir(parents=True,exist_ok=True)
ARCHIVE_ROOT=ROOT/'archives'; ARCHIVE_ROOT.mkdir(parents=True,exist_ok=True)
MAX_ARCHIVE_MEMBERS=200
MAX_ARCHIVE_UNCOMPRESSED=100 * 1024 * 1024
def auth(a):
 if a != f'Bearer {os.environ["I3S_FILE_SERVICE_KEY"]}': raise HTTPException(401,'Unauthorized')
def path(n):
 p=ROOT/Path(n).name
 if not p.suffix: raise HTTPException(400,'Filename needs an extension')
 return p
def artifact(p):
 mime={'.xlsx':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','.docx':'application/vnd.openxmlformats-officedocument.wordprocessingml.document','.pptx':'application/vnd.openxmlformats-officedocument.presentationml.presentation','.pdf':'application/pdf','.csv':'text/csv','.png':'image/png','.txt':'text/plain','.md':'text/markdown','.html':'text/html'}.get(p.suffix,'application/octet-stream')
 return [{'status':'success','filename':p.name,'download_url':f'/files/{p.name}'}, f'data:{mime};base64,' + base64.b64encode(p.read_bytes()).decode()]
def safe_archive_members(z):
 infos=[i for i in z.infolist() if not i.is_dir()]
 if len(infos)>MAX_ARCHIVE_MEMBERS: raise HTTPException(400,'Archive has too many members')
 if sum(i.file_size for i in infos)>MAX_ARCHIVE_UNCOMPRESSED: raise HTTPException(400,'Archive expands beyond safe limit')
 for i in infos:
  member=Path(i.filename)
  if member.is_absolute() or '..' in member.parts or '\\' in i.filename or (i.external_attr >> 16) & 0o170000 == 0o120000:
   raise HTTPException(400,'Archive contains an unsafe member')
 return infos
class Doc(BaseModel): filename:str; title:str=''; paragraphs:list[str]=[]; tables:list[list[list[str]]]=[]
@app.post('/create_docx')
def docx(x:Doc,authorization:str=Header('')):
 auth(authorization); p=path(x.filename); d=Document(); d.add_heading(x.title,0)
 for q in x.paragraphs:d.add_paragraph(q)
 for rows in x.tables:
  t=d.add_table(rows=len(rows),cols=len(rows[0]));
  for i,r in enumerate(rows):
   for j,v in enumerate(r):t.cell(i,j).text=str(v)
 d.save(p); return artifact(p)
class Sheet(BaseModel): name:str='Sheet1'; columns:list[str]; rows:list[list[object]]=[]; formulas:dict[str,str]={}
class Xlsx(BaseModel): filename:str; sheets:list[Sheet]
@app.post('/create_xlsx')
def xlsx(x:Xlsx,authorization:str=Header('')):
 auth(authorization); p=path(x.filename); w=Workbook(); w.remove(w.active)
 for s in x.sheets:
  q=w.create_sheet(s.name);q.append(s.columns)
  for r in s.rows:q.append(r)
  for cell,formula in s.formulas.items():q[cell]=formula
 w.save(p);return artifact(p)
class Text(BaseModel): filename:str; content:str
@app.post('/create_text_file')
def text(x:Text,authorization:str=Header('')):
 auth(authorization);p=path(x.filename);p.write_text(x.content);return artifact(p)
@app.post('/create_csv')
def csvf(x:Xlsx,authorization:str=Header('')):
 auth(authorization);p=path(x.filename);s=x.sheets[0]
 with p.open('w',newline='') as f: csv.writer(f).writerows([s.columns,*s.rows])
 return artifact(p)
@app.post('/create_pptx')
def pptx(x:Doc,authorization:str=Header('')):
 auth(authorization);p=path(x.filename);r=Presentation()
 for title in ([x.title]+x.paragraphs):
  s=r.slides.add_slide(r.slide_layouts[0]);s.shapes.title.text=title
 r.save(p);return artifact(p)
@app.post('/create_pdf')
def pdf(x:Doc,authorization:str=Header('')):
 auth(authorization);p=path(x.filename);d=FPDF(format='A4');d.set_auto_page_break(auto=True,margin=15);d.add_page()
 font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';d.add_font('DejaVu','',font);d.set_font('DejaVu',size=16)
 d.multi_cell(0,10,str(x.title),new_x=XPos.LMARGIN,new_y=YPos.NEXT)
 d.set_font('DejaVu',size=11)
 for q in x.paragraphs:d.multi_cell(0,7,str(q),new_x=XPos.LMARGIN,new_y=YPos.NEXT)
 d.output(p);return artifact(p)
class Chart(BaseModel): filename:str; labels:list[str]; values:list[float]; title:str='Chart'
@app.post('/create_chart')
def chart(x:Chart,authorization:str=Header('')):
 auth(authorization);p=path(x.filename);plt.bar(x.labels,x.values);plt.title(x.title);plt.tight_layout();plt.savefig(p);plt.close();return artifact(p)
@app.get('/files/{name}')
def get(name:str,authorization:str=Header('')):
 auth(authorization);p=path(name);return FileResponse(p,filename=p.name)

# Toolbox processing endpoints deliberately accept only filenames already in the
# dedicated /data volume. They never accept paths, URLs, or executable commands.
class Existing(BaseModel): filename:str
class Convert(BaseModel): filename:str; output_format:str
class Resize(BaseModel): filename:str; width:int; height:int
class ArchiveCreate(BaseModel): filename:str; members:list[str]
def existing(n):
 p=path(n)
 if not p.is_file(): raise HTTPException(404,'File not found in Toolbox volume')
 return p
def run(args,timeout=90):
 try:return subprocess.run(args,check=True,capture_output=True,text=True,timeout=timeout)
 except (subprocess.CalledProcessError,subprocess.TimeoutExpired) as e: raise HTTPException(400,f'Processing failed: {str(e)[:240]}')
@app.post('/inspect_document')
def inspect_document(x:Existing,authorization:str=Header('')):
 auth(authorization);p=existing(x.filename); out={'filename':p.name,'size':p.stat().st_size,'mime':magic.from_file(str(p),mime=True)}
 if p.suffix.lower()=='.pdf': out['pages']=len(PdfReader(str(p)).pages)
 elif p.suffix.lower()=='.xlsx': out['sheets']=__import__('openpyxl').load_workbook(p,read_only=True).sheetnames
 return out
@app.post('/convert_document')
def convert_document(x:Convert,authorization:str=Header('')):
 auth(authorization);p=existing(x.filename); ext=x.output_format.lower().lstrip('.')
 if ext not in {'pdf','docx','xlsx','pptx','txt','csv'}: raise HTTPException(400,'Unsupported output format')
 out=path(p.stem+'.'+ext); run(['libreoffice','--headless','--convert-to',ext,'--outdir',str(ROOT),'-env:UserInstallation=file:///tmp/lo',str(p)])
 if not out.is_file(): raise HTTPException(400,'Conversion produced no file')
 return artifact(out)
@app.post('/analyze_csv')
def analyze_csv(x:Existing,authorization:str=Header('')):
 auth(authorization);d=pd.read_csv(existing(x.filename));return {'columns':d.columns.tolist(),'rows':len(d),'summary':d.describe(include='all').fillna('').to_dict()}
@app.post('/analyze_xlsx')
def analyze_xlsx(x:Existing,authorization:str=Header('')):
 auth(authorization);d=pd.read_excel(existing(x.filename));return {'columns':d.columns.tolist(),'rows':len(d),'summary':d.describe(include='all').fillna('').to_dict()}
@app.post('/inspect_image')
def inspect_image(x:Existing,authorization:str=Header('')):
 auth(authorization);im=Image.open(existing(x.filename));return {'format':im.format,'width':im.width,'height':im.height,'mode':im.mode}
@app.post('/ocr_image')
def ocr_image(x:Existing,authorization:str=Header('')):
 auth(authorization);return {'text':pytesseract.image_to_string(Image.open(existing(x.filename)))}
@app.post('/resize_image')
def resize_image(x:Resize,authorization:str=Header('')):
 auth(authorization);p=existing(x.filename);im=Image.open(p);im.thumbnail((max(1,x.width),max(1,x.height)));out=path(p.stem+'_resized'+p.suffix);im.save(out);return artifact(out)
@app.post('/convert_image')
def convert_image(x:Convert,authorization:str=Header('')):
 auth(authorization);p=existing(x.filename);ext=x.output_format.lower().lstrip('.')
 if ext not in {'png','jpg','jpeg','webp'}:raise HTTPException(400,'Unsupported image format')
 out=path(p.stem+'.'+ext);Image.open(p).convert('RGB').save(out);return artifact(out)
@app.post('/inspect_audio')
def inspect_audio(x:Existing,authorization:str=Header('')):
 auth(authorization);p=existing(x.filename);return json.loads(run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(p)]).stdout)
@app.post('/transcribe_audio')
def transcribe_audio(x:Existing,authorization:str=Header('')):
 auth(authorization);p=existing(x.filename); model=os.getenv('WHISPER_MODEL_PATH','').strip()
 if not model or not Path(model).is_dir() or not str(Path(model).resolve()).startswith(str(ROOT.resolve())+'/'):
  raise HTTPException(501,'Whisper runtime is installed; configure an approved local model below /data before transcription is enabled')
 try:
  from faster_whisper import WhisperModel
  probe=json.loads(run(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(p)]).stdout)
  duration=float(probe.get('format',{}).get('duration',0))
  device=os.getenv('WHISPER_DEVICE','cpu')
  compute_type=os.getenv('WHISPER_COMPUTE_TYPE','int8')
  segments,info=WhisperModel(model,device=device,compute_type=compute_type).transcribe(str(p),vad_filter=True,word_timestamps=False)
  rows=[{'start':round(s.start,2),'end':round(s.end,2),'text':s.text.strip()} for s in segments]
  return {'language':info.language,'language_probability':round(info.language_probability,3),'duration_seconds':round(duration,2),'segments':rows,'transcript':' '.join(s['text'] for s in rows)}
 except Exception as e: raise HTTPException(400,f'Transcription failed: {str(e)[:240]}')
@app.post('/inspect_video')
def inspect_video(x:Existing,authorization:str=Header('')): return inspect_audio(x,authorization)
@app.post('/extract_keyframes')
def extract_keyframes(x:Existing,authorization:str=Header('')):
 auth(authorization);p=existing(x.filename);out=path(p.stem+'_keyframe_001.jpg');run(['ffmpeg','-y','-i',str(p),'-vf','select=eq(pict_type\\,I)','-frames:v','1',str(out)]);return artifact(out)
@app.post('/transcribe_video')
def transcribe_video(x:Existing,authorization:str=Header('')): return transcribe_audio(x,authorization)
@app.post('/analyze_video')
def analyze_video(x:Existing,authorization:str=Header('')):
 auth(authorization);return {'metadata':inspect_audio(x,authorization),'vision_backend':'not configured','note':'On-demand local Qwen3-VL requires a separately approved isolated inference route; no vision model is kept loaded.'}
@app.post('/list_archive')
def list_archive(x:Existing,authorization:str=Header('')):
 auth(authorization);p=existing(x.filename)
 if p.suffix.lower()!='.zip':raise HTTPException(400,'Only zip archives are accepted')
 with zipfile.ZipFile(p) as z:return {'members':[i.filename for i in safe_archive_members(z)]}
@app.post('/extract_archive')
def extract_archive(x:Existing,authorization:str=Header('')):
 auth(authorization);p=existing(x.filename)
 if p.suffix.lower()!='.zip':raise HTTPException(400,'Only zip archives are accepted')
 destination=ARCHIVE_ROOT/p.stem
 destination.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(p) as z:
  infos=safe_archive_members(z); names=[i.filename for i in infos]
  for i in infos:
   target=(destination/i.filename).resolve()
   if not str(target).startswith(str(destination.resolve())+'/'): raise HTTPException(400,'Archive member escapes destination')
   target.parent.mkdir(parents=True,exist_ok=True)
   with z.open(i) as src, target.open('wb') as dst: shutil.copyfileobj(src,dst,1024*1024)
 return {'extracted':names}
@app.post('/create_archive')
def create_archive(x:ArchiveCreate,authorization:str=Header('')):
 auth(authorization);out=path(x.filename)
 if out.suffix.lower()!='.zip':raise HTTPException(400,'Archive filename must end .zip')
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
  for n in x.members:
   p=existing(n);z.write(p,p.name)
 return artifact(out)
