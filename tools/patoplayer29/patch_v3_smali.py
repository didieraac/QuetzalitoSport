#!/usr/bin/env python3
"""Pato Player 29 V3: eliminar pantallas publicitarias restantes.
Interviene exclusivamente clases de SDK de anuncios y deja intactas las
Activities y WebViews de reproducción.
"""
from pathlib import Path
import re
import sys

def unique_file(root, suffix):
    matches=[p for p in Path(root).rglob("*.smali") if p.as_posix().endswith(suffix)]
    if len(matches)!=1:
        raise RuntimeError(f"Se esperó una clase para {suffix}: {matches}")
    return matches[0]

def replace_method(filepath, method_name, params, new_body, required_super=None):
    s=filepath.read_text()
    regex=re.compile(
        r"(?m)^(?P<header>\.method[^\n]*\s"+re.escape(method_name)+r"\("+re.escape(params)+r"\)V)\n"
        r"(?P<body>.*?)^\.end method$",
        re.S|re.M,
    )
    matches=list(regex.finditer(s))
    if len(matches)!=1:
        raise RuntimeError(f"Firma no única: {filepath} {method_name}({params}): {len(matches)}")
    match=matches[0]
    if required_super and required_super not in s:
        raise RuntimeError(f"Superclase inesperada {filepath}")
    replacement=match.group("header")+"\n"+new_body.rstrip()+"\n.end method"
    s=s[:match.start()]+replacement+s[match.end():]
    filepath.write_text(s)
    print(f"Bloqueado {filepath.name}::{method_name}({params})")

def main(root):
    # Al abrir anuncios de pantalla completa, cerrar inmediatamente su propia
    # Activity, sin permitir que se construya ni se muestre la creatividad.
    for suffix in [
        "/com/google/android/gms/ads/AdActivity.smali",
        "/com/startapp/sdk/ads/interstitials/OverlayActivity.smali",
    ]:
        f=unique_file(root,suffix)
        s=f.read_text()
        m=re.search(r"(?m)^\.super (L[^;\n]+;)$",s)
        if not m:
            raise RuntimeError("No se encontró superclase")
        parent=m.group(1)
        # Originalmente se llama onCreate en la superclase: preservar ciclo de vida
        body=(
            "    .locals 0\n\n"
            f"    invoke-super {{p0, p1}}, {parent}->onCreate(Landroid/os/Bundle;)V\n\n"
            "    invoke-virtual {p0}, Landroid/app/Activity;->finish()V\n\n"
            "    return-void"
        )
        replace_method(f,"onCreate","Landroid/os/Bundle;",body,required_super=parent)

    # Las funciones internas de carga de anuncios App Open / Interstitial
    # reciben void y pueden ser anuladas sin tocar devolución ni UI de la app.
    for suffix,methods in [
        ("/com/google/android/gms/ads/appopen/AppOpenAd.smali",[
            ("b","Landroid/content/Context;Ljava/lang/String;Lcom/google/android/gms/ads/AdRequest;ILcom/google/android/gms/ads/appopen/AppOpenAd$AppOpenAdLoadCallback;"),
            ("c","Landroid/content/Context;Ljava/lang/String;Lcom/google/android/gms/ads/AdRequest;Lcom/google/android/gms/ads/appopen/AppOpenAd$AppOpenAdLoadCallback;"),
        ]),
        ("/com/google/android/gms/ads/interstitial/InterstitialAd.smali",[
            ("b","Landroid/content/Context;Ljava/lang/String;Lcom/google/android/gms/ads/AdRequest;Lcom/google/android/gms/ads/interstitial/InterstitialAdLoadCallback;"),
        ]),
    ]:
        f=unique_file(root,suffix)
        for name,params in methods:
            replace_method(f,name,params,"    .locals 0\n\n    return-void")
    print("V3: métodos publicitarios desactivados sin cambiar código del reproductor.")

if __name__=="__main__":
    main(sys.argv[1])
