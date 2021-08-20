import requests
import json
from bs4 import BeautifulSoup as bs

TRIENNALE = "https://www.unimi.it/it/corsi/corsi-di-laurea-triennali-e-magistrali-ciclo-unico"
MAGISTRALE = "https://www.unimi.it/it/corsi/corsi-di-laurea-magistrale"
INSEGNAMENTI = "https://www.unimi.it/it/corsi/insegnamenti-dei-corsi-di-laurea/insegnamenti-dei-corsi-di-laurea-2021-2022"

# For now each department is mapped this way 'cause I can't be bothered to properly extract data from an external CSS
DIPARTIMENTI = {
        "areacard-C": "SU",
        "areacard-Z": "SM",
        "areacard-A": "G",
        "areacard-E": "SF",
        "areacard-D": "MC",
        "areacard-H": "MV",
        "areacard-B": "SPES",
        "areacard-G": "SAA",
        "areacard-F": "ST",
        "areacard-M": "SMLC",
        "areacard-K": "K",
}

# triennale
cdl_triennale = []

resp = requests.get(TRIENNALE)
data = bs(resp.text, "lxml").find(class_="view-cercacorsi").find("div", class_="view-content")
data = data.find_all("div", class_="corso")

for corso in data:
    for x in corso.div.div.div.div["class"]:
        if x.startswith("areacard"):
            dip = DIPARTIMENTI[x]

    content = corso.div.div.div.div.div.find(class_="card-content")
    content.find(class_="card_center").find(class_="sede").clear()
    cdl_triennale.append({
        "dipartimento": dip,
        "anno": content.find(class_="anno-accademico").string,
        "corso": content.find(class_="bp-title").a.string,
        "sito": "https://unimi.it" + content.find(class_="bp-title").a["href"],
        "tipo": content.find(class_="card_left").div.get_text().replace("\n", "").strip(),
        "lingua": content.find(class_="card_center").get_text().replace("\n", "").strip()
    })

fd = open("cdl_triennale.json", "w")
fd.write(json.dumps(cdl_triennale))
fd.close()
