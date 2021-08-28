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
            "faculty": fac,
            "department": get_departments(dip),
            "year": content.find(class_="anno-accademico").string,
            "degree": content.find(class_="bp-title").a.string,
            "site": "https://unimi.it" + content.find(class_="bp-title").a["href"],
            "type": content.find(class_="card_left").div.get_text().replace("\n", "").strip(),
            "language": content.find(class_="card_center").get_text().replace("\n", "").strip()
        })
    return result


def get_departments(link):
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


def get_courses():
    params = (
        ('_wrapper_format', 'drupal_ajax'),
    )
    
    data_req = {
      'page': 0,
      'title': '',
      'uof_lingua_target_id': 'All',
      'uof_ssd_target_id': 'All',
      'view_name': 'w4_af',
      'view_display_id': 'block_5',
      'view_args': '2022',
      'view_path': '/node/41344',
      'view_base_path': '',
      'view_dom_id': '8ec2ef8e824c1d7311a41f68f678bc736369e463afb055b3ae3ba04a78ab0739',
      'pager_element': '0',
      '_drupal_ajax': '1',
      'ajax_page_state[theme]': 'unimi',
    }

    result = []
    itera = 0
    
    while(True):
        data_req["page"] = itera
        resp = requests.post(COURSES, params=params, data=data_req)
        
        data = bs(resp.json()[4]["data"], "lxml")
        data = data.find("tbody")
        if data is None:
            break
        for row in data.find_all("tr", class_="bottom10"):
            inner = row.find("td", class_="views-field-view")
            profs = []
            for x in inner.div.find_all("div", class_="views-row"):
                try:
                    for y in x.find("div", class_="views-field-uof-persons").div.find_all("a"):
                        profs.append(y.string.strip())
                except Exception:
                    pass
        
            title = row.find("td", class_="views-field-title").a
            course = {
                    "title": title.string.strip(),
                    "slug": title["href"].split("/")[-1].strip(),
                    "profs": profs,
                    "language": row.find("td", class_="views-field-uof-lingua").string.strip(),
                    "cfu": row.find("td", class_="views-field-cfu").string.strip()
            }
            result.append(course)
        itera += 1
    return result


TRIENNALE = "https://www.unimi.it/it/corsi/corsi-di-laurea-triennali-e-magistrali-ciclo-unico"
MAGISTRALE = "https://www.unimi.it/it/corsi/corsi-di-laurea-magistrale"
COURSES = "https://www.unimi.it/it/views/ajax"

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

    # courses
    fd = open("courses.json", "w")
    fd.write(json.dumps(get_courses()))
    fd.close()

if __name__ == "__main__":
    main()
