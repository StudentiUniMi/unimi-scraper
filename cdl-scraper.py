import json
import requests
from bs4 import BeautifulSoup as bs


class Degree():
    def __init__(self, name, link):
        self.name = name
        self.link = link


HOME = "https://www.unimi.it"

PERIODS = {
    "" : 0,
    "Periodo non definito" : 0,
    "Periodo non specificato" : 0,
    "Primo semestre" : 1,
    "Primo trimestre" : 1,
    "Primo quadrimestre" : 1,
    "Secondo semestre" : 2,
    "Secondo trimestre" : 2,
    "Secondo quadrimestre" : 2,
    "Secondo annuale" : 2,
    "Terzo trimestre" : 3,
    "Terzo quadrimestre" : 3,
    "Su più periodi" : 4,
    "annuale" : 4,
}

PERIOD_TYPES = {
    "semestre" : "Semestre",
    "trimestre" : "Trimestre",
    "quadrimestre" : "Quadrimestre"
}

YEARS = {
    "Anno: 1" : 1,
    "Anno: 2" : 2,
    "Anno: 3" : 3,
    "Anno: 4" : 4,
    "Anno: 5" : 5,
    "Anno: 6" : 6,
    "Anno di corso a scelta dello studente" : -2
}

OBBLIGATORIO = ["Obbligatorio", "Insegnamenti obbligatori"]

DIV = {
    "ugov-of-pd-special-i" : "Obbligatorio",
    "ugov-of-pd-rules" : "x",
    "ugov-of-pd-special-f": ""
}


def parser(LINK):
    # Faccio la richiesta alla pagina principale con tutti i CdL
    data = requests.get(LINK).text
    soup = bs(data, "lxml").find_all("a", hreflang = "it")

    degrees = [Degree(link.text.lstrip().rstrip(), HOME + link["href"]) for link in soup][1:]
    # Salvo ogni CdL con i relativi insegnamenti in una lista
    results = []
    specials = [
        "Progettazione delle aree verdi e del paesaggio - Interateneo",
        "Scienze viticole ed enologiche - Interateneo",
        "Artificial Intelligence"
    ]

    # Eseguo il parse di ogni CdL
    for degree in degrees:
        print(degree.name)
        # Corsi a parte
        if degree.name in specials:
            index = degree.link[::-1].find("/")
            slug = degree.link[::-1][:index][::-1].replace("-", "_")
            degree = {
                "name" : degree.name,
                "slug" : slug,
                "link" : degree.link,
                "curriculums" : ""
            }
            results.append(degree)
            continue
        # Faccio la richiesta alla pagina del CdL
        data = requests.get(degree.link).text
        soup = bs(data, "lxml")
        # Estraggo il div che contiene le tabelle con i corsi
        div = soup.find("div", class_ = "field field--name-ugov-piano-didattico field--type-map field--label-hidden field--item")
        # Estraggo i curriculum dai toggle presenti; vanno esclusi i toggle che danno indicazioni sulle propedeuticità
        curriculums = [
            a.text.lstrip().rstrip() for a in div.find_all("a", attrs = {"data-toggle" : "collapse", "data-parent" : "#curr-accordion"})
                if a.text.lstrip().rstrip() != "Propedeuticità del curriculum"
        ]
        # Se ho un solo curriculum allora va denominato come "Curriculum unico"
        if len(curriculums) == 1:
            curriculums[0] = "Curriculum unico"
        else:
            for s in range(len(curriculums)):
                curriculums[s] = curriculums[s][12:]
        # Estraggo tutte le tabelle presenti nel div
        all_tables = div.find_all("div", class_ = "panel-body")
        tables = []
        # Se ho una sola tabella non devo parsare altro; se le due tabelle hanno stessa lunghezza va bene lo stesso
        # Altrimenti vanno tolte le tabelle che indicano una propedeuticità
        if len(all_tables) == 1:
            tables = all_tables
        elif len(all_tables) == len(curriculums):
            tables = all_tables
        else:
            for table in all_tables:
                if table.find("div", class_ = "panel-body") != None:
                    tables.append(table)
        # Creo una lista che conterrà tutti i curriculum
        all_curriculums = []
        # assert len(tables) == len(curriculums) VERIFICATO
        # Lavoro con un indice per avere gestione parallela sulle liste tables e curriculums
        for i in range(len(tables)):
            # Creo una lista che conterrà tutti gli insegnamenti
            all_courses = []
            table = tables[i]
            # Estraggo dalla navbar le indicazioni sugli anni
            # Metto un try-except perchè alcuni corsi della magistrale non hanno la navbar con le indicazioni sui periodi
            try:
                ul = table.find("ul", class_ = "nav nav-tabs ugov-of-pd-years").find_all("li")
            except:
                # In caso di assenza della navbar, estraggo i div con una classe diversa
                all_table_contents = [special_div for special_div in table.find_all("div")]
                table_contents = []
                # Devo rimuovere tutti i div che non hanno class contenuta in DIV e quelli che non hanno classe
                # Uso un try-except per non avere un KeyError
                for special_div in all_table_contents:
                    try:
                        div_class = special_div["class"][0]
                    except:
                        continue
                    else:
                        if div_class in DIV.keys():
                            table_contents.append(special_div)
                # L'anno lo metto come a scelta dello studente
                years = ["Anno di corso a scelta dello studente" for i in range(len(table_contents))]
            else:
                years = [year.text.lstrip().rstrip() for year in ul]
                # Estraggo tutti i div che contengono la tabella principale per ogni anno
                all_table_contents = [content for content in table.find("div", class_ = "tab-content").find_all("div")]
                table_contents = []
                # Devo rimuovere i div che non mi servono: sono quelli che non hanno un attributo class
                for x in all_table_contents:
                    div_class = ""
                    try:
                        # Prendo l'indice 0 perchè ["class"] splitta la classe rispetto a " "
                        div_class = x["class"][0]
                    except:
                        continue
                    if div_class == "tab-pane":
                        table_contents.append(x)
                # assert len(table_contents) == len(years) VERIFICATO
            # Lavoro con un indice per avere gestione parallela sulle liste table_contents e years
            for t in range(len(table_contents)):
                content = table_contents[t]
                # Estraggo le tabelle relative a ogni periodo
                subtables = content.find_all("table", class_ = "no-more-tables")
                # Il periodo dell'anno è contenuto dei div don class "top30 titoletto"
                periods = content.find_all("div", class_ = "top30 titoletto")
                # Se non ho estratto niente vuol dire che sono nei corsi speciali della magistrale
                # La lista verrà riempita di sole x, il motivo è spiegato più avanti
                if len(periods) == 0:
                    periods = ["x" for i in range(len(subtables))]
                else:
                    # Elimino possibili tabelle che non hanno un div con class "top30 titoletto"
                    subtables = subtables[:len(periods)]
                    # Ripulisco eventuali spazi a destra e a sinistra del testo nel tag
                    for p in range(len(periods)):
                        periods[p] = periods[p].text.lstrip().rstrip()
                    # assert len(subtables) == len(periods) VERIFICATO OVVIAMENTE, FACCIO IO IN MODO CHE SIANO UGUALI
                    # Estraggo ora dei div che contengono sempre dei corsi complementari
                    # Uso un try-except poichè questi div non sono sempre presenti
                    try:
                        complementary = content.find("div", class_ = "top30 ugov-of-pd-rules").find_all("table", class_ = "no-more-tables")
                        # assert len(complementary) < 2 VERIFICATO METTENDO FIND_ALL AL POSTO DI FIND E SENZA IL SECONDO FIND_ALL
                    except:
                        pass
                    else:
                        # Aggiungo le tabelle complementari a quelle che ho già
                        subtables += complementary
                        # Vado a rendere le tabelle periods e subtables uguali in numero di elementi
                        # Faccio l'append di un valore che non sta nelle chiavi del dict PERIODS
                        # Se non è presente infatti il periodo se lo va a estrarre da solo dalla tabella quando viene creato il dict da mettere nel JSON
                        while len(periods) < len(subtables):
                            periods.append("x")
                # Da ogni tabella estraggo tutti i td
                # Lavoro con un indice per avere gestione parallela sulle liste subtables e years
                for k in range(len(subtables)):
                    # Prendo il tipo dell'insegnamento, per adesso dal periodo
                    # Nel caso il tipo è scritto dentro la tabella verrà cambiato dopo
                    course_type = periods[k]
                    # Se il corso è un'attività conclusiva allora lo escluso, non essendoci un gruppo per quelli
                    if course_type == "Attività conclusive":
                        continue
                    subtable = subtables[k]
                    # Estraggo il corpo della tabella con tutte le righe
                    courses = subtable.find("tbody").find_all("tr")
                    for course in courses:
                        # Provo a estrarre il tipo del corso dal dizionario
                        try:
                            # Vedo in che div sono; in base a questo assegno un course type
                            course_type = DIV[content["class"][0]]
                        except:
                            pass
                        # Provo a estrarre il tipo del corso da un td particolare
                        try:
                            # Forzo l'estrazione: se va a buon fine ho estratto il tipo del corso
                            # Se ha esito negativo allora è un corso e si deve far riferimento al tipo scritto in precedenza
                            course_type = course.find("td", colspan = "5").text
                        except:
                            pass
                        else:
                            continue
                        try:
                            # Forzo l'estrazione degli elementi che mi interessano
                            # In ogni caso viene fatto perchè viene fatto un raise di una Exception senza motivo
                            # Infatti appena viene catturata l'eccezione si ha il pass
                            name = course.find("a").text
                            link = HOME + course.find("a")["href"]
                            cfu = course.find("td", attrs = {"data-title" : "Crediti"}).text
                            lang = course.find("td", attrs = {"data-title" : "Lingua"}).text
                        except:
                            pass
                        # Se la prova finale (tesi) e i tirocini sono in altre tabelle diverse da "Attività conclusive" le vado a escludere
                        if name == "Prova finale" or "Tirocinio" in name or "tirocinio" in name or "Stage" in name or "stage" in name:
                            continue
                        # Estraggo lo slug prendendo la parte finale di ogni link e facendo il replace di - con _
                        index = link[::-1].find("/")
                        slug = link[::-1][:index][::-1].replace("-", "_")
                        # Creo l'elemento che identifica un insegnamento
                        course = {
                            "name" : name,
                            "slug" : slug,
                            "link" : link,
                            "year" : YEARS[years[t]],
                            "period" : PERIODS[periods[k]] if periods[k] in list(PERIODS.keys()) else PERIODS[course.find("td", attrs = {"data-title" : "Periodo"}).text],
                            "complementary": False if course_type in OBBLIGATORIO else True,
                            "cfu" : cfu,
                            "lang" : lang,
                            "editions" : [
                                {
                                    "n_edition" : "",
                                    "profs" : []
                                }
                            ]
                        }
                        # Metto l'elemento nella lista di tutti gli insegnamenti
                        all_courses.append(course)
            # Vado a rimuovere i duplicati, o meglio, gli insegnamenti che sono su più anni (solo pochi CdL hanno sta roba)
            no_duplicates = []
            visited = []
            for c in range(len(all_courses)-1):
                current_course = all_courses[c]
                # Se il nome dell'insegnamento è già stato analizzato passo al successivo
                if current_course["name"] in visited:
                    continue
                # Dichiaro la lista che conterrà tutti gli anni
                all_periods = [current_course["year"]]
                for d in range(c+1, len(all_courses)):
                    # Se ho stesso nome e l'anno non è ancora stato trovato vado a mettere l'anno tra quelli possibili
                    if current_course["name"] == all_courses[d]["name"] and all_courses[d]["year"] not in all_periods:
                        all_periods.append(all_courses[d]["year"])
                current_course["year"] = all_periods if len(all_periods) > 1 else all_periods[0]
                # Metto il corso sistemato nella nuova vista
                no_duplicates.append(current_course)
                # Aggiorno i corsi visitati
                visited.append(current_course["name"])
            # Creo l'elemento che identifica un curriculum
            curriculum = {
                "name" : curriculums[i],
                "courses" : no_duplicates if len(no_duplicates) > 1 else no_duplicates[0]
            }
            # Metto l'elemento nella lista di tutti i curriculum
            all_curriculums.append(curriculum)
        # Estraggo ancora una volta lo slug, stavolta del CdL
        index = degree.link[::-1].find("/")
        slug = degree.link[::-1][:index][::-1].replace("-", "_")
        # Creo l'elemento che identifica un CdL
        degree = {
            "name" : degree.name,
            "slug" : slug,
            "link" : degree.link,
            "curriculums" : all_curriculums
        }
        # Metto l'elemento nella lista di tutti i CdL
        results.append(degree)
    return results


def main():
    TRIENNALE = "https://www.unimi.it/it/corsi/corsi-di-laurea-triennali-e-magistrali-ciclo-unico"
    MAGISTRALE = "https://www.unimi.it/it/corsi/corsi-di-laurea-magistrale"

    ft = open("insegnamenti_per_cdl_triennale.json", "w")
    ft.write(json.dumps(parser(TRIENNALE)))
    ft.close()

    ft = open("insegnamenti_per_cdl_magistrale.json", "w")
    ft.write(json.dumps(parser(MAGISTRALE)))
    ft.close()


if __name__ == "__main__":
    main()
