from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.ticker import MaxNLocator
arial = Path('/System/Library/Fonts/Supplemental/Arial.ttf')
if arial.exists():
    font_manager.fontManager.addfont(arial)
plt.rcParams.update({'font.family':['Arial', 'Helvetica', 'Liberation Sans'],'font.size':11,'svg.fonttype':'none'})
fig,axes=plt.subplots(3,1,figsize=(10,5.2))
metrics=[('Database-backed owner response (s)',[19.76,2.63],['19.76 s','2.63 s']),('Application RSS (MiB)',[304.4,125.9],['304.4 MiB','125.9 MiB']),('Complete deployment size (MB)',[65.607443,9.775305],['65.6 MB','9.8 MB'])]
for ax,(title,values,labels) in zip(axes,metrics):
 ax.barh([1,0],values,height=.42,color=['#727b77','#4d963d'])
 ax.set_yticks([1,0],['Spring','CoilBase'])
 ax.set_xlim(0,max(values)*1.3)
 ax.set_ylim(-.6,1.6)
 ax.set_title(title,loc='left',fontsize=12,pad=8)
 for y,v,label in zip([1,0],values,labels): ax.text(v+max(values)*.025,y,label,va='center',fontsize=11)
 ax.xaxis.set_major_locator(MaxNLocator(4))
 ax.grid(axis='x',color='#e5e9e6'); ax.set_axisbelow(True)
 ax.tick_params(axis='both',length=0,labelsize=10)
 for spine in ax.spines.values(): spine.set_visible(False)
fig.subplots_adjust(left=.14,right=.97,top=.94,bottom=.06,hspace=.65)
fig.savefig(Path(__file__).resolve().parents[1] / 'docs/images/results.svg',facecolor='white')
