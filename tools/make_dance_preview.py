"""Generate an original dance arrangement using the app's overview analyzer."""
import math,random,sys
from array import array
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from faderlogic.waveform import analyze_samples
rng=random.Random(128);rate=22050;duration=128;pcm=array('h')
for n in range(rate*duration):
    t=n/rate;beat=t/(60/128);phase=(beat%1)*(60/128)
    if t<16:level=.45+.4*t/16
    elif t<48:level=1.
    elif t<64:level=.16+.08*math.sin(t*.5)
    elif t<80:level=.25+.6*(t-64)/16
    elif t<112:level=.95+.05*math.sin(t*1.8)
    else:level=.85-.5*(t-112)/16
    pump=.6+.4*(1-math.exp(-phase*20))
    kick=.7*math.exp(-phase*20)*math.sin(2*math.pi*(49*phase+4*(1-math.exp(-phase*30))))
    bass=.36*pump*(math.sin(2*math.pi*55*t)+.25*math.sin(2*math.pi*110*t))
    chord=.17*pump*(math.sin(2*math.pi*440*t)+.7*math.sin(2*math.pi*660*t)+.4*math.sin(2*math.pi*990*t))
    offbeat=((beat-.5)%.5)*(60/128)
    noise=rng.uniform(-1,1)
    hats=(.11+.24*math.exp(-offbeat*65))*noise+.07*math.sin(2*math.pi*6500*t)
    clap=.3*math.exp(-((beat-1)%2)*(60/128)*28)*noise
    if 48<=t<64:kick*=.05;bass*=.25;hats*=.2
    if 64<=t<80:clap+=.25*(t-64)/16*math.exp(-(beat%.25)*(60/128)*55)*noise
    value=math.tanh(1.6*level*(kick+bass+chord+hats+clap))*.94
    pcm.append(round(value*32767))
bars=tuple(tuple(round(v,5) for v in row) for row in analyze_samples(pcm))
(ROOT/'faderlogic/dance_preview.py').write_text('"""Original 128 BPM example, processed with the same 256-bin overview analyzer as tracks.\nGenerated offline by tools/make_dance_preview.py.\n"""\nDANCE_PREVIEW = '+repr(bars)+'\n',encoding='utf8')
print('Generated',len(bars),'overview bins using the production analyzer')
