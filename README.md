# Biblias libres para Lámpara

Textos de la Biblia de dominio público o con licencia libre, en el formato que descarga la app
Lámpara. Aquí solo hay textos bíblicos; el código de la app no está en este repositorio.

Cada archivo se preparó con `preparar_biblias.py` desde la fuente indicada (fijada en un
commit). El texto no se cambió: solo se quitaron marcas de formato (notas al pie, referencias
cruzadas y títulos de sección) y se pasó a JSON. La huella SHA-256 de cada archivo está en
`informe.json`, junto con los controles de versículos.

| Archivo | Versión | Licencia | Fuente |
|---|---|---|---|
| es/rv1865.json | Reina-Valera 1865 | Dominio público | scrollmapper/bible_databases |
| es/oso1569.json | Biblia del Oso (Casiodoro de Reina, 1569), ortografía original | CC0 (transcripción) / dominio público | palabra-de-dios/Biblia-del-Oso-1569 |
| es/vbl.json | Versión Biblia Libre | CC BY-SA 4.0 | yojananyosef/spavbl_app |
| es/blm.json | Santa Biblia libre para el mundo (borrador) | Dominio público (CC0) | kahunapule/spablm |
| es/bes.json | La Biblia en Español Sencillo | CC BY 4.0 | wldeh/bible-api (eBible.org) |
| en/kjv.json | King James Version (Pure Cambridge Edition) | Public domain | scrollmapper/bible_databases |
| en/bsb.json | Berean Standard Bible | CC0 | scrollmapper/bible_databases |
| en/nheb.json | New Heart English Bible | Public domain | scrollmapper/bible_databases |
| en/asv.json | American Standard Version (1901) | Public domain | scrollmapper/bible_databases |
| en/ylt.json | Young's Literal Translation (1898) | Public domain | scrollmapper/bible_databases |
| en/darby.json | Darby Bible (1889) | Public domain | scrollmapper/bible_databases |
| en/webster.json | Webster Bible (1833) | Public domain | scrollmapper/bible_databases |
| en/bbe.json | Bible in Basic English (1949/1964) | Public domain | scrollmapper/bible_databases |
| en/geneva1599.json | Geneva Bible (1599) | Public domain | scrollmapper/bible_databases |
| pt/blivre.json | Bíblia Livre | CC BY 3.0 BR | scrollmapper/bible_databases |
| fr/darby-fr.json | Bible J.N. Darby (1885) | Domaine public | scrollmapper/bible_databases |
| de/elb1905.json | Elberfelder Bibel (1905) | Gemeinfrei | scrollmapper/bible_databases |

## Créditos que piden las licencias

- Versión Biblia Libre. Copyright © 2018-2020 Jonathan Gallagher y Shelly Barrios de Avila.
  Licencia Creative Commons Atribución-CompartirIgual 4.0 (https://creativecommons.org/licenses/by-sa/4.0/).
  Este archivo es una adaptación de formato bajo la misma licencia.
- La Biblia en Español Sencillo. © 2018 AudioBiblia.org / Irma Flores.
  Licencia Creative Commons Atribución 4.0 (https://creativecommons.org/licenses/by/4.0/).
- Bíblia Livre, licenciada sob Creative Commons Atribuição 3.0 Brasil (CC BY 3.0 BR).
- Berean Standard Bible: dedicada al dominio público (CC0).

## Avisos de calidad

- Biblia del Oso: la transcripción todavía no tiene Ester ni Daniel, y usa la numeración y
  la ortografía de 1569 (ſ, u por v).
- Santa Biblia libre para el mundo: su autor la marca como borrador; le faltan Ezequiel 5:17
  y 10:13-22 en la fuente.
- Algunas traducciones modernas no incluyen versículos que faltan en los manuscritos más
  antiguos (por ejemplo Mateo 17:21). No es un error.
