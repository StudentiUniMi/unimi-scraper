import requests
import json
from bs4 import BeautifulSoup as bs


def parse_data(data):
    result = []
    for corso in data:
        for x in corso.div.div.div.div["class"]:
            if x.startswith("areacard"):
                fac = FACOLTA[x]
    
        content = corso.div.div.div.div.div.find(class_="card-content")
        content.find(class_="card_center").find(class_="sede").clear()
        dip = content.find(class_="card-bottom").div.div.a["href"].strip()

        # The only case that enters in this branch is with the course of AI, it is on "unipv.it"
        if "unimi.it" not in dip:
            dip = None

        result.append({
            "facolta": fac,
            "dipartimento": get_dipartimento(dip),
            "anno": content.find(class_="anno-accademico").string,
            "corso": content.find(class_="bp-title").a.string,
            "sito": "https://unimi.it" + content.find(class_="bp-title").a["href"],
            "tipo": content.find(class_="card_left").div.get_text().replace("\n", "").strip(),
            "lingua": content.find(class_="card_center").get_text().replace("\n", "").strip()
        })
    return result


def get_dipartimento(link):
    if link is None:
        return ""
    resp = requests.get(
            link,
            headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36"}
    )
    if resp.status_code != 200:
        raise Exception("Couldn't fetch the page")
    data = bs(resp.text, "lxml")
    dip = data.find(class_="bgcolor-PRINCIPALE")
    if dip is None:
        dip = data.find(class_="bgcolor-ASSRESPONS")
    if dip is None:
        return ""
    dip = dip.div.div.a.string.strip()
    return dip


TRIENNALE = "https://www.unimi.it/it/corsi/corsi-di-laurea-triennali-e-magistrali-ciclo-unico"
MAGISTRALE = "https://www.unimi.it/it/corsi/corsi-di-laurea-magistrale"
INSEGNAMENTI = "https://www.unimi.it/it/corsi/insegnamenti-dei-corsi-di-laurea/insegnamenti-dei-corsi-di-laurea-2021-2022"

# For now each faculty is mapped this way 'cause I can't be bothered to properly extract data from an external CSS
FACOLTA = {
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


def main():
    # triennale
    resp = requests.get(TRIENNALE)
    if resp.status_code != 200:
        raise Exception("Couldn't fetch the page")
    data = bs(resp.text, "lxml").find(class_="view-cercacorsi").find("div", class_="view-content")
    data = data.find_all("div", class_="corso")
    
    cdl_triennale = parse_data(data)
    
    fd = open("cdl_triennale.json", "w")
    fd.write(json.dumps(cdl_triennale))
    fd.close()
    
    # magistrale
    resp = requests.get(MAGISTRALE)
    if resp.status_code != 200:
        raise Exception("Couldn't fetch the page")
    data = bs(resp.text, "lxml").find(class_="view-cercacorsi").find("div", class_="view-content")
    data = data.find_all("div", class_="corso")

    cdl_magistrale = parse_data(data)

    fd = open("cdl_magistrale.json", "w")
    fd.write(json.dumps(cdl_magistrale))
    fd.close()


if __name__ == "__main__":
    main()
