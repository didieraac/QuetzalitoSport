#!/usr/bin/env python3
"""Adaptación TV de un APK V7 ya parcheado y decodificado con apktool."""
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

A = lambda name: '{http://schemas.android.com/apk/res/android}' + name

def apply(folder):
    root=Path(folder)
    manifest=root/'AndroidManifest.xml'
    tree=ET.parse(manifest)
    app=tree.getroot().find('application')
    assert app is not None
    activities={a.get(A('name')):a for a in app.findall('activity')}
    for name in ('SplashActivity','WelcomeActivity','MainActivity'):
        activities['com.dhapps.quetzalsport.'+name].set(A('screenOrientation'),'landscape')
    splash=activities['com.dhapps.quetzalsport.SplashActivity']
    fi=next(f for f in splash.findall('intent-filter') if any(c.get(A('name'))=='android.intent.category.LAUNCHER' for c in f.findall('category')))
    if not any(c.get(A('name'))=='android.intent.category.LEANBACK_LAUNCHER' for c in fi.findall('category')):
        ET.SubElement(fi,'category',{A('name'):'android.intent.category.LEANBACK_LAUNCHER'})
    icon=app.get(A('icon'))
    assert icon
    app.set(A('banner'),icon)
    manifest.write_bytes(ET.tostring(tree.getroot(),encoding='utf-8',xml_declaration=True))

    smali=root/'smali/n1/g.smali'
    s=smali.read_text()
    original='    new-instance v4, Landroidx/recyclerview/widget/LinearLayoutManager;'
    call='    invoke-direct {v4, v5}, Landroidx/recyclerview/widget/LinearLayoutManager;-><init>(I)V'
    assert s.count(original)==1 and s.count(call)==1
    offset=s.index(original)
    assert 'MainActivity;->O:Landroidx/recyclerview/widget/RecyclerView;' in s[offset-700:offset]
    s=s.replace(original,'    new-instance v4, Landroidx/recyclerview/widget/GridLayoutManager;',1)
    s=s.replace(call,'''    const/4 v5, 0x3

    invoke-direct {v4, v5}, Landroidx/recyclerview/widget/GridLayoutManager;-><init>(I)V

    const/4 v5, 0x1''',1)
    smali.write_text(s)

    landscape=root/'res/layout-land'
    landscape.mkdir(exist_ok=True)
    tv=ET.parse(root/'res/layout/view_canales.xml')
    hdr=tv.getroot().find('LinearLayout').find('LinearLayout')
    hdr.set(A('paddingTop'),'6.0dip')
    hdr.set(A('paddingBottom'),'4.0dip')
    hdr.findall('TextView')[0].set(A('textSize'),'22.0sp')
    for field in tv.iter('EditText'):
        field.set(A('focusableInTouchMode'),'false')
    for rv in tv.iter('androidx.recyclerview.widget.RecyclerView'):
        rv.set(A('descendantFocusability'),'afterDescendants')
        rv.set(A('focusable'),'false')
    (landscape/'view_canales.xml').write_bytes(ET.tostring(tv.getroot(),encoding='utf-8',xml_declaration=True))

    card=ET.parse(root/'res/layout/item_canal_card.xml')
    card.getroot().set(A('layout_marginBottom'),'10.0dip')
    inner=card.getroot().find('LinearLayout')
    inner.set(A('minHeight'),'76.0dip')
    for widget in inner.findall('TextView'):
        if widget.get(A('id'))=='@id/tvNombre':
            widget.set(A('textSize'),'17.0sp')
    (landscape/'item_canal_card.xml').write_bytes(ET.tostring(card.getroot(),encoding='utf-8',xml_declaration=True))
    print('TV preparado: Leanback launcher, landscape, D-pad, 3 columnas')

if __name__=='__main__':
    apply(sys.argv[1])
