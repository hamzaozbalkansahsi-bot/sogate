# Proje      : SEXSOGATE
# Geliştirici: PTYS Technoligess LLC
# Tasarım    : Hamza ÖZBALKAN
# Dosya      : scripts/build-pdf-fonts.py
# Açıklama   : PDF için lisanslı web fontlarından sabit ağırlıklı TTF türetir.
"""SIL OFL bildirimlerini koruyan yerel font türetimi."""
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

target = Path('assets/fonts')
target.mkdir(parents=True, exist_ok=True)
for source, family in [('montserrat', 'SexsogateBody'), ('playfairdisplay', 'SexsogateDisplay')]:
    font = instantiateVariableFont(TTFont(f'public/fonts/{source}-variable.woff2'), {'wght': 400}, inplace=True)
    font.flavor = None
    values = {1: family, 2: 'Regular', 3: f'SEXSOGATE:{family}:20261110', 4: f'{family} Regular', 6: f'{family}-Regular', 16: family, 17: 'Regular'}
    font['name'].names = [record for record in font['name'].names if record.nameID not in values]
    for name_id, value in values.items():
        font['name'].setName(value, name_id, 3, 1, 0x409)
    font.save(target / f'{family}-Regular.ttf')
print('PDF font türetimi tamamlandı; telif/lisans kayıtları korunuyor.')
