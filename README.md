# Elmix – steg för steg (ingen kodkunskap behövs)

Resultatet: en webbadress du kan dela, som uppdaterar sig själv varje måndag.

## Engångsjobb (ca 10 minuter)

1. **Skapa konto** på https://github.com (gratis).
2. Klicka **+** uppe till höger → **New repository**.
   - Namn: `elmix`
   - Välj **Public**
   - Klicka **Create repository**.
3. Klicka **uploading an existing file**, och dra in ALLA filer och mappar från den uppackade
   `elmix`-mappen (`app.py`, `build.py`, `requirements.txt`, `templates`, `.gitignore`, `README.md`).
   Klicka **Commit changes**.
4. **Viktigt – den dolda mappen `.github`:** den följer ofta inte med när man drar in filer
   (särskilt på Mac). Lägg då in den för hand:
   - Klicka **Add file → Create new file**.
   - Skriv som filnamn exakt: `.github/workflows/update.yml`
     (när du skriver `/` blir det mappar automatiskt).
   - Klistra in hela innehållet från filen `update.yml` som du fick i zip-filen.
   - Klicka **Commit changes**.
5. Gå till **Settings → Pages**. Under **Build and deployment → Source**, välj **GitHub Actions**.
6. Gå till fliken **Actions**. Om den frågar, klicka **I understand my workflows, enable them**.
   Välj **Uppdatera elmix** i listan till vänster → **Run workflow** → **Run workflow**.
7. Vänta 1–2 minuter tills bollen blir grön. Din adress är då:
   `https://DITT-ANVÄNDARNAMN.github.io/elmix/`
   (den visas även under Settings → Pages). Dela den med vem du vill.

## Därefter
- Sidan **uppdateras automatiskt varje måndag**. Du behöver inte göra något.
- Vill du uppdatera direkt: **Actions → Uppdatera elmix → Run workflow**.
- Längst ner på sidan står när den senast byggdes.
- GitHub stänger av schemalagda körningar i repon som varit helt orörda i 60 dagar.
  Får du ett mejl om det: gå till Actions och klicka **Enable workflow**.

## Om något går fel
Gå till **Actions**, klicka på den röda körningen och kopiera felmeddelandet.

## Köra lokalt (valfritt)
- Live-version med Flask: `pip install -r requirements.txt` och `python app.py`
- Bygga den statiska sidan: `python build.py` → öppna `dist/index.html`
