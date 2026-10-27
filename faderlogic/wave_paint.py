"""Combined DJ waveforms and explicit split-lane designs from measured features."""
import math
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QBrush, QFont, QLinearGradient, QPainter, QPainterPath, QPen
from .theme import COLORS

THREE_BAND = ('#167DFF','#FF9D28','#F2F6FF')
LEGACY = tuple(COLORS[k] for k in ('wave_low','wave_mid','wave_high'))
RGB = ('#F74450','#40E776','#3F9CFF')
SPLIT_STYLES = ('split_bars','split_ribbon')




def rgb_colour(bar):
    weights=[max(0.,float(v)) for v in bar[:3]]
    largest=max(.001,max(weights))
    # A dominant band is saturated; genuinely broadband energy blends to white.
    return QColor(*[min(255,18+int(237*(value/largest)**1.2)) for value in weights])


def draw_waveform(p,w,h,bars,style,mode):
    if style=='spectrogram':
        draw_spectrum(p,w,h,bars,mode)
        return
    if style in SPLIT_STYLES:
        draw_split(p,w,h,bars,style,mode)
        return
    if style=='classic' and mode=='faderlogic':
        # The original FaderLogic waveform remains available without a redesign.
        for i,row in enumerate(bars):
            x=(i+.5)*w/len(bars)
            for amp,colour,scale in zip(row[:3],LEGACY,(.42,.32,.22)):
                p.setPen(QPen(QColor(colour),max(1.,w/len(bars)-1.2),Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap))
                p.drawLine(QPointF(x,h/2-amp*h*scale),QPointF(x,h/2+amp*h*scale))
        return
    shared_bands=mode in ('bands','faderlogic')
    palette=THREE_BAND if mode=='bands' else LEGACY
    layers=range(3) if shared_bands else (None,)
    # All these amplitude styles share one centreline, never three lanes.
    mid=h-3 if style=='segmented' else h/2
    span=h-17 if style=='segmented' else h*.45
    if style=='line': span=h*.23
    if style=='segmented': draw_segments(p,w,h,bars)
    elif style=='enhanced':
        p.setPen(QPen(QColor(104,135,166,30),.5))
        for f in (.25,.5,.75): p.drawLine(QPointF(0,h*f),QPointF(w,h*f))
    count=len(bars)
    for band in layers:
        amplitudes=[min(1.,max(0.,row[band] if band is not None else row[-1] if len(row)>27 else max(row[:3]))) for row in bars]
        colours=[QColor(palette[band]) if band is not None else rgb_colour(row) if mode=='rgb' else QColor(COLORS['cyan']) for row in bars]
        gradient=QLinearGradient(0,0,w,0)
        for i,c in enumerate(colours): gradient.setColorAt(i/max(1,count-1),c)
        if style in ('classic','enhanced'):
            pen_w=max(1.,w/count-(1.5 if style=='classic' else 2.2))
            for i,(amp,c) in enumerate(zip(amplitudes,colours)):
                x=(i+.5)*w/count
                half=amp*span
                if half<.05: continue
                if style=='classic':
                    p.setPen(QPen(c,pen_w,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap))
                    p.drawLine(QPointF(x,mid-half),QPointF(x,mid+half))
                else:
                    glow=QColor(c);glow.setAlpha(55)
                    p.setPen(QPen(glow,pen_w+3,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap))
                    p.drawLine(QPointF(x,mid-half),QPointF(x,mid+half))
                    vertical=QLinearGradient(0,mid-half,0,mid+half)
                    vertical.setColorAt(0,c.lighter(130));vertical.setColorAt(.5,c.darker(130));vertical.setColorAt(1,c)
                    p.fillRect(QRectF(x-pen_w/2,mid-half,pen_w,half*2),vertical)
                    p.setPen(QPen(c.lighter(145),max(.7,pen_w)))
                    p.drawLine(QPointF(x,mid-half),QPointF(x,mid-half+.7))
        else:
            upper,lower,fill=envelope_paths(amplitudes,w,mid,span,mirror=style!='segmented')
            if style in ('filled','multilayer','segmented'):
                p.setOpacity(.48 if style=='multilayer' else .92)
                p.fillPath(fill,QBrush(gradient)); p.setOpacity(1)
            if style in ('line','multilayer'):
                for width,alpha in ((6,.10),(3,.22),(.85,1.)):
                    p.setOpacity(alpha);p.setPen(QPen(QBrush(gradient),width))
                    p.drawPath(upper);p.drawPath(lower)
                p.setOpacity(1)
            elif style=='filled':
                # Fine spectral-coloured lip keeps this a smooth continuous body.
                p.setPen(QPen(QBrush(gradient),.65));p.drawPath(upper);p.drawPath(lower)
            if style=='multilayer' and (band is None or band==2):
                rms=[sum(amplitudes[max(0,i-4):i+5])/len(amplitudes[max(0,i-4):i+5]) for i in range(count)]
                a,b,_=envelope_paths(rms,w,mid,span)
                p.setPen(QPen(QColor(230,245,255,190),.7));p.drawPath(a);p.drawPath(b)
                # Thin peak ticks distinguish peaks from the smoothed envelope.
                p.setPen(QPen(QColor(230,245,255,85),.5))
                for i in range(0,count,4):
                    x=i*w/max(1,count-1)
                    peak=min(1.,bars[i][-1] if len(bars[i])>27 else max(bars[i][:3]))
                    p.drawLine(QPointF(x,mid-peak*span),QPointF(x,mid-peak*span-2))
    p.setPen(QPen(QColor(165,202,225,55),.5));p.drawLine(QPointF(0,mid),QPointF(w,mid))


def envelope_paths(amplitudes,w,mid,span,mirror=True):
    upper,lower,fill=QPainterPath(),QPainterPath(),QPainterPath()
    n=len(amplitudes)
    points=[QPointF(i*w/max(1,n-1),mid-amp*span) for i,amp in enumerate(amplitudes)]
    bottom=[QPointF(i*w/max(1,n-1),mid+amp*span if mirror else mid) for i,amp in enumerate(amplitudes)]
    upper.moveTo(points[0]);lower.moveTo(bottom[0])
    for i in range(1,n):
        # Catmull-style cubic interpolation: a continuous energy envelope.
        a,b=points[i-1],points[i]; dx=(b.x()-a.x())/3
        upper.cubicTo(QPointF(a.x()+dx,a.y()),QPointF(b.x()-dx,b.y()),b)
        a,b=bottom[i-1],bottom[i]
        lower.cubicTo(QPointF(a.x()+dx,a.y()),QPointF(b.x()-dx,b.y()),b)
    fill.addPath(upper)
    for point in reversed(bottom): fill.lineTo(point)
    fill.closeSubpath()
    return upper,lower,fill


def draw_segments(p,w,h,bars):
    n=len(bars);groups=max(1,min(10,w//105))
    energy=[max(row[:3]) for row in bars];high=max(.001,max(energy))
    for group in range(groups):
        section=energy[group*n//groups:(group+1)*n//groups]
        level=sum(section)/max(1,len(section))/high
        label='Quieter' if level<.3 else 'Medium' if level<.65 else 'Stronger'
        x=group*w/groups
        p.fillRect(QRectF(x,0,w/groups-2,h),QColor(36,89,113,20+int(30*level)))
        p.setPen(QPen(QColor(152,183,207,70),.6));p.drawLine(QPointF(x,0),QPointF(x,h))
        p.setPen(QColor('#B2C0D0'));p.setFont(QFont('Segoe UI',6))
        p.drawText(QRectF(x+5,0,w/groups-8,12),Qt.AlignmentFlag.AlignLeft,label)


def draw_split(p,w,h,bars,style,mode):
    n=len(bars);height=h/3
    palette=THREE_BAND if mode=='bands' else RGB if mode=='rgb' else LEGACY if mode=='faderlogic' else (COLORS['cyan'],)*3
    for band in range(3):
        top=band*height;mid=top+height/2
        p.fillRect(QRectF(0,top,w,height-1),QColor(18+band*3,25+band*3,34+band*3,180))
        values=[min(1.,max(0.,row[band])) for row in bars]
        c=QColor(palette[band])
        if style=='split_bars':
            p.setPen(QPen(c,max(.8,w/n-1.),Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap))
            for i,amp in enumerate(values):
                x=(i+.5)*w/n;half=amp*(height/2-2)
                p.drawLine(QPointF(x,mid-half),QPointF(x,mid+half))
        else:
            a,b,path=envelope_paths(values,w,mid,height/2-2)
            gradient=QLinearGradient(0,top,0,top+height)
            gradient.setColorAt(0,c);gradient.setColorAt(.5,c.darker(180));gradient.setColorAt(1,c)
            p.fillPath(path,gradient);p.setPen(QPen(c.lighter(125),.6));p.drawPath(a);p.drawPath(b)
        p.setPen(QColor('#E8EEF7'));p.setFont(QFont('Segoe UI',5))
        p.drawText(QRectF(3,top,30,height),Qt.AlignmentFlag.AlignVCenter,('LOW','MID','HIGH')[band])


def draw_spectrum(p,w,h,bars,mode):
    from .waveform import FREQUENCY_EDGES
    if len(bars[0])<27:
        p.setPen(QColor(COLORS['muted']));p.drawText(QRectF(0,0,w,h),Qt.AlignmentFlag.AlignCenter,'Spectral analysis unavailable')
        return
    n=len(bars)
    for i,row in enumerate(bars):
        for j,power in enumerate(row[3:27]):
            frequency=math.sqrt(FREQUENCY_EDGES[j]*FREQUENCY_EDGES[j+1])
            band=0 if frequency<250 else 1 if frequency<2500 else 2
            if mode=='normal': c=QColor(COLORS['cyan'])
            elif mode in ('bands','faderlogic'): c=QColor((THREE_BAND if mode=='bands' else LEGACY)[band])
            else:
                f=j/23*2;a=min(1,int(f));f-=a
                colours=[QColor(colour) for colour in RGB]
                c=QColor(*[int(getattr(colours[a],name)()*(1-f)+getattr(colours[a+1],name)()*f) for name in ('red','green','blue')])
            c.setAlpha(int(max(0.,min(1.,power))*255))
            p.fillRect(QRectF(i*w/n,h-(j+1)*h/24,w/n+.2,h/24+.2),c)
    p.setFont(QFont('Segoe UI',5));p.setPen(QColor('#FFFFFF'))
    for label,y in (('10 kHz',0),('1 kHz',h*.43),('40 Hz',h-10)):
        p.drawText(QRectF(3,y,40,10),Qt.AlignmentFlag.AlignLeft,label)
