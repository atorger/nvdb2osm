
# Import av Trafikverkets NVDB-data till OpenStreetMap

Detta är README-filen till nvdb2osm.py, ett skript som konverterar
nedladdat NVDB-data (i SHP-format) till en OSM XML-fil.

Det körs på kommandoraden:

`nvdb2osm.py <katalog eller zip-arkiv med NVDB shape-filer> <output.osm>`

Exempel:

Dela upp länsfilen till kommuner:
`split_nvdb_data.py --lanskod_filter 25 Norrbottens_län_Shape.zip output`

Konvertera en kommun till OSM:
`nvdb2osm.py -v --municipality_filter Luleå --railway_file=Järnvägsnät_grundegenskaper.zip output/Luleå.zip luleå.osm`

Kör kommandot utan argument för att se vilka flaggor man kan sätta. I
exemplet används `-v` för att visa INFO-loggar.

Det tar cirka en kvart att tugga igenom en kommun (lägger man till
parametern `--skip_self_test` går det betydligt fortare). Arkiven med
shape-filer laddas ner från Trafikverket. Man går till
https://lastkajen.trafikverket.se/
I skrivande stund är minsta filerna per län så de behöver delas upp
först, vilket man kan göra med split_nvdb_data.py-skriptet.

Skriptet lägger inte till järnväg (järnväg kartläggs lämpligen
separat), men för att kunna lägga järnvägskorsningar på rätt position
behöver skriptet ändå det nationella järnvägsnätet. Den filen hittas
också på lastkajen: Järnvägsnät_grundegenskaper.zip
Det är en fil för hela Sverige så man använder samma för alla
kommuner.

Skriptet kräver vissa tredjepartsmoduler, listade i requirements.txt,
installera med `pip install -r requirements.txt`

För generell Python-användning och installation får man Googla :-)


Tips för Windows 10-installation
--------------------------------

Anaconda för python gör det enklare:

    conda install geopandas
    conda install sortedcontainers
    pip install scanf


Hur importen går till
---------------------

1. Ladda ner paketerat NVDB-data från https://lastkajen.trafikverket.se/
2. Dela upp datat i mindre delar med split_nvdb_data.py-skriptet
2. Konvertera datat till OSM-format med nvdb2osm.py-skriptet
3. Ladda in resultatet som ett eget lager i JOSM
   (dela upp det i mindre delar)
4. Ladda ner existerande OSM-karta för motsvarande område till eget
   lager i JOSM
5. Förbered existerande OSM-data för att sammanfogas med NVDB
6. Sammanfoga lagren, och ladda upp

Att ladda ner och köra det här skriptet är ett litet jobb, det stora
jobbet är att sammanfoga det manuellt med existerande. Har man inte
möjlighet/kunskap att köra Python-skript kan man kanske be någon annan
köra skripet för det område man är intresserad av för att få en
OSM-fil som man sen kan jobba med.


Bakgrund
--------

När OSM startades var det inte vanligt att det fanns publika data av
den kvalitet som finns idag i många länder. Tanken var att en stor
mängd frivilliga skulle manuellt rita alla vägar baserat på flygfoton
och egna GPS-spår.

Idag används de traditionella manuella teknikerna parallellt med att
man importerar data från olika publika databaser. Importer är
internationellt sett ett känsligt ämne, då många inom OSM fortfarande
tycker att databasen endast borde innehålla manuellt arbete gjort av
oss själva. Delvis på grund av det finns det fortfarande inga
funktioner i OSM för att använda externa datakällor och automatisk
synkronisera dessa när de uppdateras.

Det innebär att importer är fortfarande till stor del ett manuellt
arbete, och varje typ av import blir ett litet utvecklingsprojekt i
sig.

Notera att tanken med import är inte att ersätta manuellt
kartläggande, utan att vara ett komplement. Antalet kartläggare i
Sverige idag är inte tillräckligt för att hålla hela landet
uppdaterat, men genom att importera en bra bas blir arbetsuppgiften
för manuell kartläggning mer rimlig.

NVDB innehåller inte allt man vill kartlägga heller, elljusspår, olika
stigar, mm finns inte, så manuell kartläggning med lokal kännedom är
fortsatt viktig och central.


Om NVDBs precision
------------------

De flesta av våra vägar finns redan i OSM, men många är kartlagda för
många år sedan när datakällorna inte var lika bra som NVDB är, så de
är ofta värda att uppdatera. Det handlar inte bara om geometrin
(alltså vägens form), utan även annan information som
hastighetsgränser, vägbeläggning, vägnamn och flera andra "taggar" som
ofta saknas eller kan vara felaktiga i vägar som kartlagts tidigare.

NVDB-datat om än bra är inte 100% perfekt. "Värsta" exemplet är bro-
och tunneldatat som uppvisar en hel del precisionsfel, i enstaka fall
kan en bro ligga flera hundra meter fel. I andra fall handlar det mer
om hur man väljer att kartlägga vid begränsat utrymme: inne i städer
där cykelvägar och vägar kartläggs nära bredvid varandra läggs de inte
alltid exakt geografiskt utan på ett sätt som ger vägarna mer
utrymme.

NVDB-datat innehåller också flera överlapp och små glapp här och var,
vilket gör det besvärligt att jobba med maskinellt, men de flesta av
dessa småfel hanteras och repareras av importskriptet.

Hursomhelst, överlag är NVDB en mycket bra datakälla med bra
precision, så man behöver i regel inte korrigera vägarna efter
flygfoton, utan snarare tvärtom kan man använda NVDB-vägarna för att
justera flygfotons position.


Om NVDBs data-taggar
--------------------

OSM har all information i samma geometri genom att man sätter en mängd
taggar på varje väg/nod. NVDB är istället organiserat i lager med
olika information, underliggande geometri är dock
densamma. Hastighetsgränser ligger i ett lager, vägnamn i ett annat
och så vidare.

Importskriptet tar alltså alla dessa lager, översätter taggarna lager
för lager och sammanfogar. Ibland överlappar information och skripet
försöker lösa dessa situationer automatiskt, vilket går i de flesta
fall. Om inte skrivs det ut en varning och en "fixme"-tag skrivs in i
resulterande OSM-fil så man kan gå in och justera manuellt.

(NVDB:s Shape-filer (.shp) går att öppna direkt i JOSM, vilket är
användbart om man vill jämföra. JOSM gör viss geometriförenkling och
tar bort dubbletter när den öppnar en Shape-fil, så håller man på
debugga sådant behöver man analysera datat på annat vis.)

NVDB har med få undantag en hög grad av korrekthet i informationen, så
den går överlag lita på när man inte har någon bättre information.
För nybyggnationer kan datat dock vara inaktuellt och där kan det
saknas geometri, eller finnas en preliminär geometri som inte är
korrekt. Ibland kan vissa lager ha ny information och andra lager har
gammal, och då kan det bli det problem i sammanfogningen, normalt
lyckas dock skriptet tugga igenom datat ändå.

Enskild väg har inte lika rik information eftersom den inte underhålls
statligt. Vägbeläggning sägs vara grus även om vägföreningen lagt
asfalt till exempel. Inom små samhällen kan det vara tvärtom,
vägbeläggningen sägs vara asfalt fastän det är grus. I vissa
(sällsynta) fall kan vägar vara så dåligt underhållna att de inte
längre är framkomliga för bilar. Där är flygfoton och lokal kännedom
till hjälp.

Många av NVDB:s taggar går att översätta mer eller mindre rakt av till
en motsvarande OSM-tag. I vissa fall har dock NVDB mer information än
vad OSM har taggar för (till exempel fordon- och trafikanttyp), och i
andra fall har NVDB mindre information än vad OSM förväntar sig
(körfältens riktning på flerfiliga vägar och vilket av flera körfält
som är för kollektivtrafik).

I ett flertal fall finns det olika tänkbara översättningslösningar,
för att se hur skriptet gör får man läsa koden.

Det är viktigt att notera att NVDB inte innehåller tillräckligt mycket
information för att göra en fullständigt bra slutledning av
highway-taggen, det gäller särskilt service, track och
unclassified, men även i viss utsträckning residential. Det innebär
att det *alltid* finns visst behov av att ändra highway-taggarna från
det skriptet kommit fram till, mer om det senare.


Kommentar om NVDB:s RLID och segmentlängd
-----------------------------------------

NVDB:s geometri har globalt unika identifierare "RLID". Dessa är
statiska och förändras inte, så man kan spåra vad som hänt med en
väg. I tidiga versioner av det här skriptet så fördes dessa
över. Vägsegmenten med ett RLID är emellertid i många fall korta,
vilket gör att vägarna blir upphuggna i små bitar. Ofta sammanfaller
det med broar, ändring av hastighetsgränser osv (som gör att det blir
uppdelning även i OSM) så i många fall blir det ändå inte fler bitar
än vad det skulle vara annars.

Testning visade dock att det är tillräckligt ofta en väg blir upphuggen
i småbitar enbart pga av RLID så därför har vi plockat bort
det. Skriptet genererar nu så långa segment som möjligt, dvs så länge
vägen inte ändrar taggar sitter det ihop i ett segment.

Trots detta blir segmenten ofta kortare än vad som finns inne i OSM nu
eftersom NVDB-skriptet har ofta högre detaljnivå (broar, ändrade
hastighetsgränser mm) som gör att taggar byts och vägarna måste delas
upp av den anledningen.

Att RLID inte förs över innebär vissa nackdelar när man ska göra
framtida uppdatering av datat. Ett uppdateringsskript måste emellertid
oavsett RLID eller ej gå in och jämföra geometrin med avancerade
algoritmer eftersom datat lever tillsammans med manuellt ritad
geometri och andra datakällor, så RLID gör inte mycket till eller från
i praktiken. I vissa specialfall hade det förvisso varit en bonus att
ha RLID kvar, men vi har gjort bedömningen att det är viktigare att
göra så långa segment som möjligt.


Tips för att sammanfoga med existerande data
--------------------------------------------

Det finns två huvudregler man måste följa när man importerar data:

 * När man ersätter existerande vägar måste man använda
   modify-operationer, antingen manuellt eller (rekommenderat) med
   hjälp av verktyget "replace geometry". Det är inte tillåtet att
   göra delete på det gamla. Anledningen till denna regel är att OSM
   loggar redigeringshistoria på varje objekt, och gör man delete så
   förstör man den.
 * NVDB-lagret ska inte ses som "facit", det måste alltid
   förbehandlas, särskilt highway-typer är inte 100% rätt. Men även
   geometri inne i trånga situationer i städer kan det finnas olika
   kreativa lösningar för och NVDB har inte alltid den bästa.

Viktigt att förstå är att "import" av detta slag är en tidskrävande
manuell process med dels justering av indatat (NVDB-lagret är inte
100% korrekt eller komplett rakt ur skriptet) och dels spårbar
modifiering av nuvarande OSM-data. Det handlar alltså *inte* om att
bara kasta bort det som finns inne nu och blint ersätta det med
NVDB-lagret.

Att sammanfoga ett nytt NVDB-lager som detta skript genererar med
existerande kartdata i OSM är en ganska avancerad uppgift, och det
hjälper om man är van att använda JOSM innan man försöker.

Tipsen på arbetsflöde som ges här utgår från att man går igenom "allt"
inom ett visst område. Man behöver inte uppdatera all geometri om man
inte vill förstås, man kan plocka ut mindre delar. Det handlar som
sagt dock inte bara om geometrin, NVDB-lagret innehåller väldigt
mycket taggar, hastighetsgränser, trafikförbud med tidsintervall osv
ofta mycket mer än vad som finns kartlagt sedan tidigare, åtminstone
på landsbygden. Därför kan det vara värdefullt att uppdatera vägar
även om de redan finns och ligger någorlunda rätt positionerade.

Det är också mycket vanligt att vägar kan vara väl positionerade på
en delsträcka, och på ett annat ställe längs samma väg ligger den 50
meter fel, så det kan löna sig att gå igenom hela vägsträckan.

Förbehandling:

Förbehandla översatt OSM-lager först, justera highway-typer särskilt
för service/track/unclassified/residential. Gå igenom alla
fixme-taggar och kör JOSM-validatorn. Tips om detta finns under
separat rubrik.

Välj ut område att jobba i:

Vissa delar i Sverige, är redan idag mycket väl uppdaterade i
OSM. Välj ut delar som har större behov av uppdatering först, och är
du nybörjare börja med en mindre komplex geometri (landsbygd istället
för stad). I städer behöver mer förbehandling av översatt OSM-lager
göras, och det finns mer tolkning av hur kartläggning ska göras (mappa
cykelvägar separat eller ej, och hur de exakt placeras i förhållande
till intilliggande väg) och det finns mer av avancerade relationer att
ta hänsyn till (busslinjer etc) - det är helt enkelt mycket gånger
svårare att jobba med stadsgeometri än landsbygd.

Se till att du jobbar på ett ställe på kartan där ingen annan håller
på just nu. Det kan nämligen bli väldigt besvärligt om två personer
håller på och redigerar kartan på samma ställe. Använd exempelvis
history-funktionen på openstreetmap.org så kan de se var folk jobbar
just nu. Försök också jobba i mindre bitar så du kan ladda upp samma
dag som du laddade ned för att redigera, ju kortare tid mellan ned-
och uppladdning desto mindre risk för kollisioner med andras
arbete. Storleksordningen 100 vägsegment åt gången brukar vara
lagom. Lite fler segment på områden där tidigare kartläggning är
sparsam, och färre åt gången där tidigare kartläggning är detaljerad.

Tyvärr finns det ingen riktigt bra funktion i OSM för att se om någon
annan redan gjort en uppdatering efter NVDB. Förr satte man
source-taggar på vägarna, men det ska man inte göra nu
längre, och changeset-source (som är där man ska ange NVDB) är bara
sökbara i 30 dagar i existerande verktyg. Det man får göra är att
visuellt inspektera. Om geometrin är lika välplacerad som NVDB, och
den är rik på taggar (hastighetsgränser, vägnamn etc) så kan man anta
att det är ett uppdaterat område.

Kontrollera positionen av existerande data:

Vissa delar av kartan är senast uppdaterad när positionsdatat i
tillgängligt källmaterial var mindre precist, man kan därför hitta
stora områden som är ganska detaljerade men som har ett offset på ett
antal tiotals meter. I vissa fall är positionsfelet så stort att man
först måste korrigera det innan man börjar arbeta med att sammanfoga,
annars kommer de exakta NDVB-vägarna gå rakt över lantbruk, sjöar och
byggnader osv. Man kan då välja att göra offset-korrigeringen i en
separat förändring och ladda upp innan du börjar jobba med importen,
eller så gör man allt på en gång, det går men blir ganska grötigt.

Modifiera inte geometrin i onödan, men gör det om du måste:

För att underlätta för framtida uppdateringar av NVDB-datat så bör man
inte modifiera NVDB-geometrin om det inte är nödvändigt. Om vägarna
ändrar form blir det svårare för ett uppdateringsskript att
matcha. Ibland måste man ändra för att spegla vad som faktiskt hänt i
verkligheten och det är okej förstås. Då det gäller specifikt broar så
ligger de ofta lite fel i NVDB och då måste man ju flytta dem. Inne i
städer kan man göra flera olika korrekta val hur man lägger
vägar/cykelvägar/gångvägar intill varandra, man kanske inte vill följa
hur NVDB gör det. Det är upp till din egen bedömning hur du gör,
säkrast är förstås att behålla stilen som var innan om den var
korrekt. Runt återvändsgränder i städer finns det olika kreativa
lösningar, och NVDB har ofta en mindre detaljerad lösning än vad man
brukar ha i OSM. Det är upp till din egen bedömning vilken lösning du
vill använda.

Välj ut en lagom stor area och sammanfoga:

Man översätter typiskt en kommun i taget med skriptet, vilket blir
för mycket att jobba med på en gång, det är oftast minst en veckas
heltidsarbete att mata in en hel kommun.

Man får dela upp lagret i JOSM, genom lite copy/paste mellan
lager. Välj en lagom stor ruta (50-200 vägar) och gör select, håll in
Alt-knappen så alla väg-segment som vidrörs också blir markerade. Det
lönar sig att kopiera smart så det blir relativt få anslutande vägar
in i området.

När du är nöjd med markeringen: välj copy, sen delete, skapa nytt
lager och välj "paste at source position". Du har nu flyttat över en
liten del av lagret till ett annat lager. Det är bra att göra en kopia
av lagret ("duplicate") så du har som referens om man blandar ihop vad
som är nytt och gammalt när man håller på och sammanfogar.

Nästa steg är att laddar du ner tillräckligt mycket karta från OSM
direkt i lagret så hela är täckt. För att göra det enklare att se var
du behöver ladda ner är ett bra trick att markera allt i lagret före
du börjar ladda ner. För att göra det enklare att komma ihåg var
gränserna går utan att behöva titta på lager-kopian så kan det vara
bra att ladda ner flera mindre rutor och följa kanterna på lagret
någorlunda istället för att ladda ner onödigt mycket data
runtomkring.

Det man nu har efter nedladdning är en enda röra :-), två kartlager på
varandra, det som finns i OSM-databasen nu, plus NVDB-lagret. Det går
ta bara en väg åt gången om man känner sig mer bekväm med det, men att
ta allt på en gång på det här sättet är betydligt effektivare. Ju mer
man jobbar desto duktigare blir man på se skillnad mellan gammal och
ny geometri och det blir mindre förvirrande att jobba, men i början
kommer det kännas lite stökigt.

JOSM har en mycket bra validator som upptäcker om man har vägar som
ligger ovanpå eller nästan ovanpå varandra, det gör att det är mycket
låg risk att man glömmer jobba igenom och sammanfoga över hela
kartan. Tvärtom är det knepigare om vägar inte fanns innan, då kan man
glömma bort att justera highway-typ eftersom man inte har någon
tidigare väg att jämföra med och validatorn ger ingen varning om man
glömmer titta på den, så var uppmärksam och jobba igenom kartan
metodiskt!

Tänk på att det inte räcker med validator-körningen som kör endast på
det egna datat vid uppladdning. Även när det är 0 varningar där kan
det vara vägar man glömt koppla ihop kvar, så man måste även köra
validatorn en gång på allt data. Då får man även varningar på det som
var kartlagt innan, men det brukar vara enkelt att skilja ut vad som
hör ihop med vad.

Använd replace geometry för att uppdatera geometri:

Om du inte redan installerat "utilsplugin2" i JOSM så gör det, för du
behöver verktyget "replace geometry". För ett uppdatera en gammal väg
med ny NVDB-geometri, gör så här:

0. Grundprincipen att följa är att varenda segment i NVDB-vägen måste
   göras replace geometry mot ett motsvarande segment i gamla
   vägen. Om inte riskerar man att bli av med taggar som fanns i gamla
   vägen för vissa segment. I de flesta fall har gamla vägen färre
   segment (saknas broar, färre taggar osv), och då måste man dela upp
   gamla vägen i motsvarande segment.
1. Markera NVDB-vägen och se hur långt segmentet är, markera
   motsvarande segment i gamla vägen.
2. Om den gamla vägen har ett mycket längre segment (perfekt passning
   inte nödvändigt), klipp upp den. OBS: klipp av på existerande nod,
   lägger man till en ny nod fungerar inte "replace geometry".
    - Var uppmärksam när du närmar dig slutet av vägen så inte segment
      i gamla vägen tar slut innan du gjort replace geometry med alla
      NVDB-segment.
    - Om den gamla vägen istället har fler segment, dela upp
      NVDB-segmentet på motsvarande vis. Om möjligt gör join på
      vägarna efter replace geometry gjorts (dvs om taggarna är precis
      samma i båda segmenten).
       - NVDB-segmentet kan man lägga till nya noder i så den kan och
         bör delas på exakt samma ställe som den gamla vägen är,
         eftersom om gamla vägen byter taggar där måste den nya göra
         det på samma ställe.
    - Var speciellt uppmärksam på broar (och tunnlar), NVDB har
      ganska ofta precisionsproblem i placeringen av dessa så man kan
      behöva justera dem manuellt.
3. Gör replace geometry, och lös eventuella tag-konflikter i dialogen
   som kommer upp.
    - Ibland har gamla vägen en relation (större vägar har oftast
      det), dessa ska behållas.
4. Upprepa segment för segment tills hela vägen är ersatt.

"Replace geometry" gör att ersättningen av den gamla geometrin görs
med modify-operationer (dvs det ser ut som man manuellt flyttat och
lagt till noder i den gamla vägen så att den exakt matchar den
nya). Detta gör att historyn av vägsegmentet behålls vilket är viktigt
för att kunna spåra förändringar, och visar respekt mot de kartläggare
som ritat vägen innan. (Historyn hamnar dock bara på ett av segmenten
när vägen behöver delas upp, men det är så OSM fungerar, det blir
likadant med manuell kalkering.)

Om vägen man ersätter innehåller noder med taggar, som till exempel
övergångsställen och vändplaner med mera, så går det inte göra
replace. Man måste då kopiera över dessa nodtaggar. Därefter går det
att göra replace geometry som vanligt. Ofta finns noderna redan
representerade i NVDB-vägen, om det är övergångsställen till exempel,
men då det gäller exempelvis vändplaner (highway=turning_circle)
saknas de ofta i NVDB. Istället för att kopiera över taggarna kan det
gå snabbare att göra flytta noden och göra merge med motsvarande nod
på nya vägen.

Vissa import-guidelines är kritiska mot replace geometry-verktyget
eftersom en sidoeffekt blir att vägen kopplas loss från anslutande
vägar som är i gamla geometrin. Istället rekommenderar man att manuellt
kalkera från ett bakgrundslager med "improve way
accuracy"-verktyget. Här tycker vi emellertid att arbetsflödet med
replace geometry beskrivet ovan ändå är bättre för att 1) manuell
kalkering är mycket långsammare, särskilt när man dessutom ska föra
över många taggar som ofta innebär att man behöver ändra segmentlängd,
2) manuell kalkering är inte lika precis, och det blir enklare att
uppdatera i framtiden både manuellt och automatiskt om man drar nytta
av det väldigt precisa geometrin NVDB erbjuder, 3) replace geometrys
nackdel med löskoppling kompenseras av validator-verktyget som ser
till att man inte missar att koppla ihop vägar, 4) löskoppling är
mindre problem än det först verkar eftersom även anslutande geometri
uppdateras i många fall.

Var upmärksam på tidigare taggar och relationer:

I vissa fall kan det vara så att tidigare kartläggning har en högre
detaljnivå på taggningen än vad importerade datat har. Red ut dessa
efter eget omdöme, ibland kan man behöva behålla det som redan finns,
och kanske dela upp NVDB-datat i fler segment för att matcha. Följ
replace-geometry-metoden ovan så går man automatiskt igenom alla
segment.

Det här import-skriptet skapar inga relations-objekt. Busslinjer,
landsvägar, olika rutter etc finns ofta redan inlagda som relationer,
se till att dessa behålls och kopplas ihop korrekt. Genom att använda
replace geometry-arbetsflödet så sköts det automatiskt.

Hantera kanter:

När man konverterar en del i taget så kommer förstås vägar längs
kanterna på området man jobbar med vara avhuggna. Det kan vara
frestande att låta dem vara okopplade eftersom man snart ska ta in
nästa del, men för att inte hamna i en situation med en trasig karta
uppladdat till OSM se till att koppla ihop vägarna längs kanterna med
existerande vägar (om de finns). Justera de existerande vägarna
istället för NVDB-vägarna, så när man tar in nästa del passar de
ihop.

Var uppmärksam på vägtyper, modifiera vid behov:

NVDB har begränsad information för att avgöra highway-typen, och den
gör inte alltid samma beslut som är lämplig för OSM. Man behöver
således ofta ändra typ manuellt.

Validatorn är din vän:

Crossing highways, disconnected ways osv. Gå igenom varningarna
ordentligt och lär dig vad de betyder. Den är bra på att upptäcka om
du har vägdubbletter eller vägar som inte är hopkopplade. Observera
att validatorn inte upptäcker alla fel om man bara kör de tester som
körs vid uppladdning. Det är en bra start, men innan du laddar upp,
kör även validatorn på all nerladdad geometri, då hittar den fel som
finns sedan tidigare också (som man kan välja rätta till eller låta
det vara som innan), men även möjligen fler fel i din sammanfogning.

Använd OSMI (OSM inspector) efteråt:

Jobbar man med stora mängder data är det validatorn till trots ändå
viss risk att något fel slinker igenom. När leverantören geofabrik
uppdaterat sin databas (de är ganska snabba) är en bra sak att gå
igenom området man uppdaterat med deras OSM inspector:
http://tools.geofabrik.de/osmi/ då kan man hitta fel som man kanske
missade med validatorn. Routing view Islands och Unconnected roads är
det som är vettigast att gå igenom. Notera att den varnar även för
sånt som inte är verkliga fel.


FIXME-taggar och JOSM Validator
-------------------------------

Skriptet lägger till fixme-taggar där det inte klarar av att lösa en
konflikt eller där NVDB inte ger tillräckligt med information. Dessa
måste man gå igenom och lösa manuellt. Använd JOSMs sökfunktion och
sök på fixme=* för att få fram all geometri som är taggad.

När skripet körs loggar den till konsollen och skriver ut "Warning:
...." när den stöter på något problem. Det kan vara bra att titta på
dessa. Oftast resulterar en Warning i en fixme-tagg i datat så det är
inte alldeles nödvändigt att gå igenom loggen.

Man *måste* använda JOSM Validator på OSM-filen för att se vilka
problem den upptäcker, och åtgärda manuellt vid behov. I stadsmiljöer
kan det vara ganska mycket som behöver manuell justering, på
landsbyggden ibland ingenting. Bro- och tunneldatat i NVDB har en del
begränsningar och precisionsproblem, kanske saknas en cykelbro osv.

Exempel på vanliga Validator-varningar, med kommentarer:

 - Barrier=yes is unspecific:
    - Begränsad NVDB-information. Kanske kan du förbättra genom
      flygfoto
 - Crossing highways:
    - Beror ofta fel/begränsningar i NVDB:s bro- och tunneldata,
      ibland saknas broar helt och hållet osv.
 - Missing tag - street with odd number of lanes:
    - På dubbelriktad väg med fler än två filer innehåller inte NVDB
      någon information om hur många filer som går i vardera
      riktning. Det går i regel lista ut från flygfoto.
 - Stub end:
    - Skriptet städar upp stumpar genom att länka ihop segment så
      långa som möjligt och ta bort små glapp, så de som ändå blir
      kvar bör man i regel lämna orörda.
 - Suspicious tag combination oneway=yes with lanes:bus:forward:
    - Felakting varning(?), att ange riktning på lanes även om vägen
      är enkelriktad verkar vara okej enligt OSM-wiki
    - Skriptet filtrar bort onödiga forward/backward i andra fall när
      vägen är enkelriktad, men behåller på lanes.
 - Way end node near other highway:
    - Kan nästan alltid ignoreras, handlar ofta om hållplatser som
      rätteligen slutar nära en annan väg
 - Overlapping highways / highway duplicated nodes / highways with
   same position:
    - I sällsynta fall har NVDB vägar med olika RLID som ligger ovanpå
      varandra. Det är så sällsynt så skripet har ingen korrigering
      för det, om det uppstår får man laga det manuellt.
 - Suspicious roundabout direction:
    - Vissa rondeller är inte helt runda och då kan JOSM tro att de
      har felaktigt taggats som rondeller. Denna varning kan man i
      regel ignorera.


Övrigt att tänka på
-------------------

Highway-typ:

NVDB har fältet "funktionell vägklass" som rangordnar vägar på en
skala 0 till 9, där 0 är de största vägarna och 9 de minsta. Vid
första anblick kan det verka som att det går att översätta direkt till
OSM:s highway-typer. För de största vägarna trunk, primary, secondary
och tertiary så mappar det rätt väl mot vad funktionell vägklass
visar. NVDB har dock flera lager som beskriver funktionell vägklass
för de stora vägarna och numreringen varierar lite beroende på
trafiktyp med mera, och dessutom kan den vara lite stökig inne i
större städer. OSM har bara en rangordning. Skriptet gör så gott det
kan, men det kommer inte alltid stämma överens med vad som finns
tidigare i OSM. Oftast är rätt val att välja det som finns
tidigare. Då det gäller motorväg och motortrafikled kan man dock lita
på NVDB för det handlar inte om subjektiv rangordning, utan om skyltad
vägtyp.

Vägtypen residential finns på ett sätt representerad i NVDB,
vägar i tätbebyggt område pekas ut specifikt och de görs till
residential av skriptet. Det blir sällan för många residential-vägar i
översättningen, men däremot för få. Större byar som inte anses vara
tätbebyggt område i NVDB ska fortfarande i regel ha residential-vägar
i OSM. Gränsen när man använder residential istället för unclassified
i en by är lite flytande och det är upp till egen bedömning. Om husen
står tätt liksom i en stad så är det en kandidat för residential. Vitt
utspridda lantbruksbyar använder man unclassified för gemensamt
brukade vägar, service för uppfarter till bostäder, och track för
övriga grusvägar och traktorspår. Vissa byar kan ha en gles
lantbruksdel och ett tättare byggt område, då kan det vara aktuellt
att använad residential på endast de vägar som är i det täta området,
man behöver alltså inte ha residential i hela byn bara för att man har
det på ett ställe.

Större vägar i städer ska ibland vara tertiary eller högre istället
för residential. Denna översättning missas ofta i NVDB-lagret eftersom
nivåerna i NVDB stämmer dåligt överens med OSM-tradition. Eftersom
städer i regel är väl kartlagda i det avseendet är det nästan alltid
bäst att använda den vägtyp som finns sedan tidigare.

I OSM i Sverige är det ganska vanligt att vägar i städers
industriområden satts till unclassified istället för residential,
medan i NVDB-lagret översätts de till residential. Efter diskussioner
med svenska kartläggare har vi kommit fram till att det är att föredra
som NVDB gör, vägar som tydligt hör ihop med själva stan ska vara
residential även om det är i ett industriområde där det inte finns
bostäder, så i det här fallet ska man alltså ändra det som fanns i OSM
tidigare. Inne i ett större samhälle och städer där gatunamn används
på alla gator kan residential användas även på kortare stumpar som
kanske varit service i en by, så länge de har gatunamn och är ansluten
till övriga residential-vägnätet.

Vägtyperna unclassified, service och track är de knepigaste för
skriptet att avgöra. Det beror på att de typerna inte mappar direkt
mot en nivå som funktionell vägklass, utan det handlar till stor del
om hur vägen används, och det finns inte den informationen in
NVDB. Genom att kombinera flera olika taggar ur NVDB-lagret och
analysera geometrin kan skriptet göra en ganska okej gissning, men det
finns garanterat behov av manuella justeringar. Hur mycket beror på
lite hur geometrin ser ut, vissa områden är svårare för skriptet att
avgöra än andra.

Unclassified ska användas för vägar som leder någonstans, till en by
eller som kopplar ihop andra större vägar, eller vägar som är mer
allmänt använda än service och viktigare än track. Den fungerar
ungefär som residential i små eller glesa byar. Inte alla vägar som
kopplar ihop ska dock vara unclassified, det måste vara rimlig bilväg
som faktiskt används nu och då, så åtminstone motsvarande track
tracktype grade3 eller bättre (oftast grade2 eller asfalt). Skriptet
kommer i vissa fall gissa fel och göra dessa som track, eller göra
vissa som borde var track till unclassified.

Track används lite speciellt i svensk kartläggningstradition. OSM
wikin är ganska luddig och inte specifikt skriven för svenska
förhållanden förstås. På många ställen i världen används track just
bara som traktorspår där man inte gärna kör bil överhuvudtaget. I
Sverige med vårt väldigt stora grusvägsnät används dock track även
till "mindre viktiga grusvägar", och vill man ange kvalitet så
använder man tracktype grade1 - grade5. Skriptet sätter inte ut grade,
eftersom den informationen inte finns i NVDB.

 Grade1: belagd väg, används nästan aldrig. Kan vara aktuell för
 gammal övergiven asfalterad väg.
 Grade2: vanlig grusväg i gott skick, inga problem att köra 70 km/h
 med vanlig bil.
 Grade3: grönsträngad grusväg, går i regel köra 70 med vanlig bil, men
 med mer försiktighet.
 Grade4: äldre mer eller mindre övergiven grusväg i dåligt skick eller
 traktorspår i lantbruket, går att köra SUV i lägre
 fart. Åkermarksvägar är typiskt framkomligare än skogsvägar med
 denna gradering.
 Grade5: ännu sämre, troligen ej framkomlig med bil, traktor
 krävs. Används även för traktorspår i lantbruket som inte är direkt
 anlagd väg utan går direkt över jordbruksmark, de är i regel
 framkomliga för bilar. Ser helt gröna ut på sommartidsflygfoto.

Om man inte anger kvalitet på sina track bör de vara grade3 eller
bättre, alltså helt okej att köra en vanlig bil på. NVDB innehåller i
regel bara sånt som motsvarar grade3 och bättre, men det finns
undantag. Lantmäteriets rasterkarta har fler vägar och också mer
information om vägens kvalitet vilket man kan se på de olika typerna
av sträckning. Använd dock flygfoto, på de riktigt små enskilda
vägarna har även lantmäteriets karta ofta fel i fråga om vägars
kvalitet.

Service-typen ska användas för vägar som leder till ett hus, strand,
camping osv. Även här är OSM-wikin lite luddig och man får titta på
svensk tradition. Vanligast i fråga om NVDB är korta snuttar som går
fram till enskilda bostadshus. Det finns ingen information i NVDB
om vilka vägar som leder till bostäder så skriptet får gissa och gör
en del fel, så vissa av vägarna blir kvar som track och behöver
manuellt uppgraderas. Där kartläggning redan gjorts är det vanligt att
det finns flera service-vägar kartlagda som inte finns i NVDB, till
exempel uppfarter och vägar inne i gårdar på industriområden och på
stora parkeringar. De måste man komma ihåg att koppla igen på när man
uppgraderar de större vägarna, och ofta finns behov att att justera
position på dem då de ofta kartlagts efter äldre flygfoton som haft
sämre positionering.

Var extra misstänksam mot långa service-vägar. En väg som går till en
telemast kan ansen vara en service-väg, men de kartläggs ofta som
allmän grusväg ändå (track) eftersom många andra använder vägen bara
för att komma åt landskapet runtomkring. Ibland kan det vara lämpligt
att låta största delen av vägen vara track/unclassified och sista
biten service.

I glesbygden kan det finnas korta vägstumpar ute i ingenstans som
används till att sätta i båtar mm. Dessa brukar lämnas som track
eftersom de inte har en frekvent och tydlig användning. Inne i byar
sätts dessa typer av vägar lämpligen till service.

I lite större byar kan skriptet tro att alla vägar ska vara service,
fast det egentligen är lämpligare med en kombination av unclassified
och service, och om byn är tätare byggd, residential.

I lantbruksbyar är det vanligt att en service-väg till ett hus
därefter ska övergå till track (kanske grade4 eller 5) när vägen leder
vidare in i lantbruket. Detta är något skriptet nästan alltid missar.

Man kan ibland bli osäker om det ska vara den ena eller andra
highway-typen. Det går inte komma ifrån att det finns knepiga
fall där där olika personer kan göra olika bedömningar. Det viktiga är
att man har en god avsikt och gör så gott man kan efter förmåga. Att
det kanske hade blivit lite annorlunda med en annan kartläggare är
okej. Det vi inte vill se är att man blint behåller det skriptet
gissat bara för att det är bekvämast.

Flerfiliga vägar:

NVDB har information om antal körfält och även antal bussfält, men
inte vilket fält som är vilket. NVDB saknar även information om vilka
fält som är till för att svänga, så turn:lanes-taggning måste man göra
själv. Ofta går det se på flygfotot vilka pilar som finns i de olika
körfälten, och om inte är turn:lanes ofta kartlagt sedan tidigare så
man kan behålla det som var.

Ibland är en flerfilig väg kartlagd som en way, ibland som två och
båda sätten är korrekt (förutsatt att taggarna är rätt satta). Ibland
har NVDB och tidigare kartläggning i OSM gjort olika val. Det är upp
till din egen bedömning vad som är lämpligt i det fallet, att antingen
behålla som det är i OSM, eller det som är i NVDB. Oftast är det
vettigast att ta alternativet med fler ways eftersom vägen i dessa
fall har stor utbredning.

Stora och flerfiliga vägar ingår ofta i route-relationer, dessa måste
man se till att de är korrekta efter man uppdaterat geometrin. När man
använder replace geometry-verktyget och matchar segment mot segment så
sköts det automatiskt. När man gör om geometrin så att den kanske går
från en way till två, måste man manuellt uppdatera rutterna.

Överlag är uppdatering av flerfiliga vägar en av de mer avancerade
uppgifterna i importarbetet.

Namn på vägar:

NVDB har skiftade kvalitet på vägnamn. Namn i städer har i regel god
kvalité, men i storleksordningen 1 av 1000 kan det vara felstavat
eller liknande, så det är bra att vara på sin vakt ändå.

Om man råkar missa något så anser vi att det är bättre att ta in
namnen oförändrade även med mindre fel som NVDB har, än att lämna
vägarna utan namn.

I vissa städer ges cykelvägarna samma namn som gatan intill, skriptet
rensar bort dessa för enligt OSM-tradition ska cykelvägarna inte ha
egna namn då. Har cykelvägen ett unikt namn behålls det.

I vissa fall har namnen rapporterats in till NVDB med endast
versaler. Skripet konverterar dessa efter bästa förmåga.

Förkortningar förekommer i vägnamnen. Norra, Södra osv förkortas ofta
till en bokstav. Vi rekommenderar att man ändrar det och skriver ut
fulla namnet om man vet vad det är. Vissa förkortningar kan man dock
behålla, som Cpl för cirkulationsplats, grv. och stv. för grenväg och
stickväg.

Skogbilvägsnätet har mindre bra kvalitet på vägnamnen. Dels är det
ganska vanligt med felstavningar, och dels är det vanligt med "lat"
namngiving typ "Granträskvägen med grenvägar". Vi rekommenderar
följande strategi:

  - Korrigera stavfel
  - Ganska ofta kan namn anges med och utan 's', exempel
    "Storlidsvägen" eller "Storlidvägen". Om man inte har mer
    information, välj alternativet som känns mer naturligt att säga,
    (gärna i lokal dialekt) för det är i regel det namnet som används.
  - Svenska namn ska vara rikssvenska, om namnet inte är specifik känt
    för dialektstavningen. Dvs om även en person som inte talar
    dialekten använder dialektnamnet så ska dialektstavningen
    användas.
  - Vägnät som namngetts i grupp med samma namn typ "X med grenvägar"
    delas helst upp så att huvudvägen heter bara X, och grenvägarna
    heter "X grv." Skogsbilvägar förlängs ofta i omgångar så ibland är
    det inte klart vilken som är huvudväg och inte, i så fall kan det
    vara säkrast att namnge alla med samma namn, alltså bara med "X",
    och lägg inte på "med grenvägar". I många fall har NVDB redan den
    typen av namnsättning, då kan man välja behålla den eller förfina
    genom att peka ut vilka som är grenvägar genom att lägga på
    "grv.".
  - Var uppmärksam på glapp, dvs att det kan vara ett par hundra meter
    utan namn och sen fortsätter det med samma namn, i de flesta fall
    är detta ett fel i NVDB och vägen ska ha samma namn även i
    glappet.
  - Då vägen nyligen förlängts kan sista delen vara utan namn. Det är
    då säkrast att lämna den utan namn istället för att använda samma
    namn som innan, eftersom det är ganska vanligt att förlängningen
    även om den bygger vidare och inte är en tydlig gren får ett nytt
    namn.

OSM har en tradition av att använda en del icke-officiella lokala
namn. Så ibland när man sammanfogar stöter man på ställen där namnet
på vägen kan vara ett helt annat än det som är i NVDB. Där är det upp
till din egna bedömning vad bästa alternativet är. Ofta är det att
behålla OSM-namnet som det är, och lägga in NVDB-namnet på
alt_name. Eller tvärtom.

Inne i städer är det vanligt att OSM och NVDB har oilka positioner på
exakt var namnet på en väg börjar och slutar. NVDB har oftast bra
kvalitet på sin namnplacering i de kommunala vägnäten. Använd egen
bedömning hur du gör när skillnader uppstår.

Cykelvägar i anslutning till gator:

NVDB kartlägger cykelväg alltid separat, även om det är i form av en
breddad trottoar. Det är också det vanligaste sättet i OSM, men ibland
så taggas cykelvägen direkt på den stora vägen. Var uppmärksam på
detta och justera vid behov. Det är upp till din egen bedömning vilken
kartläggningsmetod som ska användas. Finns plats är det i regel bättre
med cykelvägen separat.

Vägbeläggning:

NVDB specar endast "belagd" eller "grus" för kommunala och enskilda
vägar (mer detaljerat för statligt underhållna vägar). "Grus" är ett
antagande och hamnar även på jordvägar mm, därför sätter skriptet
"surface=unpaved" för dessa vägar. För "belagd" är sannolikheten så
hög att det är någon form av asfalt att surface=asphalt används. För
kullersten mm får man således ändra manuellt.

(I OSM idag är "surface=gravel" vanlig som beteckning på grusvägar,
men enligt OSM-wiki avser det knytnävsstora stenar, så egentligen inte
rätt. Bättre är då "surface=fine_gravel".)

Vändplaner:

NVDB saknar vändplaner i skogsbilvägsnätet, så de måste man lägga till
manuellt. De syns på Lantmäteriets rasterkarta.

Vändplaner på lite större vägar finns ofta i NVDB men är så dåligt
placerade att de importeras inte av skriptet (de kartläggs i NVDB som
"vändmöjlighet" och är alltså inte en exakt specifikation var
vändplanen i fråga faktiskt ligger). Så titta gärna på flygfoton inne
byar mm där vändplaner kan förväntas finnas och lägg till vid
behov. Dessa vändplaner finns i regel inte i rasterkartan heller.

Återvändsgränder med vändplan i städer är inte heller kartlagda i
NVDB (ej heller i rasterkartan), så de får man lägga till manuellt.

Vägar som slutar med återvändsgränd eller vändplan ritas i NVDB oftast
lite väl långt, till slutet av vändplanen medan OSM-tradition är att
sluta vägen mitt på vändplanen. Är man noggrann bör man matcha
positionen mot (positionsjusterat) flygfoto och det innebär i flesta
fall kan man korta av vägen något för att matcha OSM-tradition.

Parkeringar:

NVDB har inga areor, så parkering när de är kartlagda är som
punkter. För parkeringsfickor, parking=layby, rekommenderar vi starkt
att man gör det som skriptet gör, dvs endast en punkt med
parking=layby bredvid vägen. I vissa fall kan det tidigare vara
kartlagt med en area, eller en punkt med en service-vägsnutt. Om det
inte är en väldigt speciell parkeringsficka (till exempel en som
dubblerar som busshållplats) så rekommenderar vi att man förenklar
till en punkt.

För andra typer av parkeringar är dock areor att rekommendera, och
dessa måste alltså kartläggas manuellt. NVDB-skripet lägger in en nod
för större rastplatser längs landsvägarna, men dessa består i
verkligheten ofta av flera parkeringar och kanske byggnader, och är
oftast redan kartlagda. Kontrollera så att all information som
NVDB-noden tillhandahåller finns i rastplatskartläggningen, och plocka
sedan bort NVDB-noden helt om parkeringen är kartlagd som en area.

Vägbommar:

Bommar som NVDB markerat med "låst grind eller bom" sätts till
barrier=gate med access=permissive. Det betyder att bommen är
generellt sett öppen, men den kanske inte är det. Om man vet att
bommen är i regel låst kan man ändra taggen till access=private (det
finns också locked=yes, men den taggen är mindre använd). Ruttverktyg
som använder OSM-data tillåter i regel ruttning via access=permissive,
men inte via access=private.

Ofta(st) är bom-typen av typen "lift_gate", men den mer generella
taggen "gate" används för säkerhets skull. Tyvärr har inte OSM en
officiell hierarki av taggar från mer generella till mer specifika
beroende på tillgänglig informationsnivå, så vilka taggar som anses
mer generella än andra är något som avgjorts informellt. Har man
kännedom om exakt typ av vägbom kan man ändra typen manuellt.

Järnvägskorsningar:

NVDB innehåller järnvägskorsningar, men de är dåligt
positionerade. Skriptet läser in järnvägsgeometrin separat och flyttar
dem till verklig korsning, om den ligger i närheten. I enstaka fall
kan korsningen vara så avlägset felplacerad att skriptet inte hittar
en korsning, och då läggs en fixme-tagg till.

I fallet en väg korsar flera spår innehåller NVDB oftast bara en
korsningspunkt och istället antal spår den korsar. Skriptet duplicerar
korsningarna vid behov för att matcha. Ibland anges felaktigt antal
spår eller så saknas korsning helt och hållet (alltid(?) för
cykelväg), och då får man lägga till manuellt. Validatorn varnar om en
väg korsar en järnväg utan korsningsnod.

Själva järnvägen läggs inte till av skriptet eftersom den av tradition
kartläggs separat från vägar av kartläggare som specialiserar sig på
just järnväg.

NVDB:s järnvägsgeometri har ibland mindre positionsfel, om en
järnvägskorsning verkar skumt placerad jämför med Lantmäteriets
rasterkarta som är mer att lita på då det gäller positionering.

Vägnummer:

I Sverige är vi vana att europavägar skrivs utan mellanslag, "E4"
istället för "E 4". För att hålla en OSM-standard över hela Europa så
genererar skriptet dock "E 4", och detta bör behållas. Länsvägar
100-499 är unika och skrivs utan länsbokstav. Länsvägar över 500 är
inte unika och därtill läggs länsbokstav (exempel "AC 1100" istället
för bara "1100"). I officiella sammanhang används länsbokstav endast
om det är nödvändigt för att undvika sammanblandning. Eftersom det ska
gå att söka i OSM-datat är det viktigt att taggar är unika därför ska
länsbokstaven vara med här.

Undernummer används sällan i olika kartor, men det finns med i OSM nu
och skriptet tar därför med dem läggs på efter huvudnumret separerat
med en punkt (exempel: "E 4.20").


Förenklingar
------------

Skriptet tar inte med all information som finns i NVDB. Ett exempel är
att det inte sätter maxspeed 50 och 70 på småvägar där hastigheten
inte är skyltad. Bredd på vägarna tas bara med på stora vägar med
mera. Korsningar på cykelväg görs om från way till node. Exakt vilket
data som tagits med och vilka förenklingar som gjorts har diskuterats
och beslutats tillsammans med vana kartläggare. Är man intresserad av
detaljer så får man kika i skriptets källkod.


Fel i NVDB-datat
----------------

NVDB-datat har mycket hög grad av korrekthet, men det är inte 100%
perfekt. Detta är några fel som observerats:

  - Bro-databasen har mycket fel, broarna kan vara 100 meter
    felplacerade eller för korta för att nå över älven. Broar kan
    saknas, särskilt för cykelvägar. Ungefär hälften av broarna
    behöver någon slags korrigering.
  - Där en bäck går under vägen i en stor vägtrumma kan ibland NVDB
    lägga in en mycket kort bro, fastän det inte är en
    brokonstruktion. Här är det bättre att ta bort bron och använda
    kulvert för bäcken.
  - Broar som korsar andra vägar kan vara hopkopplade felaktigt i
    korsningen.
  - Gatunamn är i hög grad korrekt, men storleksordningen 1 av 1000
    kan vara felstavat eller liknande, för skogsbilväg mer än så.
  - I enstaka fall görs anpassning av geometrin för att ge utrymme i
    kartan, till exempel när cykelvägar går bredvid vägen inne i en
    stad kan vägen vara lagd några meter åt sidan om verkligheten.
  - I sällsynta fall (storleksordningen 1 ställe per kommun) kan en
    väg ha en liten parallelförlyttning med sväng där det egentligen
    ska vara en perfekt raksträcka.
      - Mer ofta kan landsvägars geometri vara lätt "vågig" när flera
        vägar ansluter i närheten av varandra, vid behov kan man
        snygga till det.
  - Enskild väg som är belagd kan vara markerad som grus
  - Vägar i små samhällen kan vara markerad som belagd fastän det är
    grus.
  - Original-datat har en hel del småglapp här och var, som skriptet
    reparerar för det mesta. I enstaka fall kan exempelvis en
    skogsväg sakna sitt vägnamn över 50 meter eller så. Dessa
    upptäcker man normalt under sammanfogningsprocessen så man kan
    manuellt korrigera dem.

Utöver rena fel så finns inte tillräcklig information i NVDB för att
göra 100% korrekt översättning av highway-typen. Highway-typ handlar
också i viss mån om personlig bedömning och i vissa fall är det
"korrekt" med flera alternativ, vilket gör att en perfekt match hade
inte varit att förvänta även om NVDB hade fullständig information.


Hålla datat uppdaterat
----------------------

NVDB är en levande databas och uppdateras hela tiden. Tanken med OSM
är att det ska finnas tillräckligt många frivilliga som håller datat
uppdaterat genom manuell kartläggning utan att behöva synka med någon
extern databas som NVDB. I praktiken finns inte så många aktiva
kartläggare i Sverige, men med NVDB inmatad i grunden finns ändå en
god chans att hålla datat fräscht på traditionellt vis - vägnätet är
ju ändå ganska statiskt. Så även om vi bara tar in NVDB-datat en gång
så lämnar i OSM-kartan i en bättre situation än den var innan.

Det finns ingen funktion i OSM för att synka automatiskt med externa
databaser, så att göra en uppdatering i framtiden skulle antagligen gå
till som så att man använder detta skript och konverterar det senaste
NVDB-datat, sen skriver man ett nytt skript som jämför detta med data
som finns inne i OSM, och därefter genererar en skillnadsfil (diff)
som man manuellt får föra över. Detta skulle man kanske göra en gång
varannat år eller så, för att komplettera sådant som kartläggare inte
hunnit uppdatera manuellt.

Detta nya skript blir troligen ganska svårt att skriva eftersom man
helst vill att det ska kunna filtrera bort justeringar i datat som
inte är faktiska förändringar utan bara förfiningar eller tillägg till
NVDB-datat, för att göra skillnadsfilen så liten som möjligt. Det är
dock inte omöjligt, särskilt med en bra grund inmatad. Det är svårare
nu i början när många av inlagda vägarna har stora offsetfel.


Information om koden
--------------------

Denna information kan bli snabbt inaktuell i och med att koden
uppdateras.

Koden är överlag ett "snabbhack", fokus på att få fram något som
fungerar så fort som möjligt snarare än att producera snygg effektiv
kod och design. Hade jag börjat om från början skulle jag troligen
försöka använda mer av shapely-biblioteket för att få effektivare
kod. Eftersom det mesta av geometriberäkningarna görs i Python-kod är
skriptet ganska långsamt.

Testning inför första release har bestått av att översätta Malmö,
Göteborg, stor-Stockholm, Umeå, Uppsala, Jokkmokk och Luleå. Även om
dessa täcker in väldigt många fall och olika typer av knepigheter i
NVDB-datat så är det troligt att skriptet kommer behöva kompletteras
ytterligare för att kunna översätta all NVDB-data i hela Sverige.

För att spara tid i bästa snabbhacksanda kör geometrikoden en massa
integritetstest på det egna datat efter förändringar, som alternativ
till en stor mängd enhetstest. Det gör att skriptet går långsammare än
det annars skulle göra. Om man orkar kan man fixa det senare (dvs ta
bort integritetstesterna och göra enhetstest på sidan om istället).

Det finns en .pylintrc så man kan köra pylint på koden.

nvdb2osm.py:

Här finns main(), alltså huvudfunktionen som kör hela processen. Grovt
sett funkar det så här:

1. Läs in ett lager med referensgeometrin och skapa en datastruktur
med denna som alla efterföljande lager matchas mot.

2. Läs in alla lager med linjegeometri, ett i taget. Direkt efter
inläsning översätts de flesta taggarna till OSM-taggar, och därefter
sammanfogas det med övriga lager, låst mot referensgeometrin. I
enstaka fall görs speciell förbehandling av lagret om det behövs, till
exempel bro- och tunnellagret.

3. Samma process görs med alla lager med punktgeometri.
Punktgeometrierna läses in efter linjegeometrin eftersom de behöver
matchas mot linjegeometrin.

4. Vissa taggar kan inte översättas direkt vid inläsning, eftersom man
behöver information från flera lager samtidigt för att kunna räkna ut
OSM-taggarna. Highway-taggarna är ett exempel. Så nästa steg är att
med hjälp av all inläst information räkna ut resterande taggar.

5. Olika typer av uppstädningar av geometri och taggar, orimligt korta
segment osv.

6. Förenkling av geometri. NVDB har väldigt många punkter i sin
geometri för att göra mjuka kurvor osv. I OSM används traditionellt
inte lika många punkter, och i detta steg förenklas geometrin för att
bättre passa stilen i OSM. Det görs inte samma förenkling för alla
objekt, rondeller behåller fler punkter än landsvägar till exempel,
precis som det brukar vara i OSM.

7. Geometrin skrivs ut till OSM XML-format, och körningen är klar.

Genom hela körningen behålls koordinatsystemet i SWEREF99, det
översätts först till WGS84 när man gör OSM XML. SWEREF99 är ett bra
koordinatsystem att jobba geometrimässigt i eftersom där är XY-baserat
och 1 enhet = 1 meter.

tag_translations.py:

Översättningsfunktioner för att konvertera NVDB-taggar i varje lager
till OSM-taggar. Detta görs direkt efter ett lager laddas in, och
innan det sammanfogas med övriga lager. Regler för hur man sammanfogar
taggar finns i merge_tags.py

merge_tags.py

När lager läggs ovanpå varandra kan ibland samma taggar kollidera, och
regler för att lösa sådana situationer finns här.

process_and_resolve.py

Här är alla funktioner som förbehandlar och efterbehandlar lagren
beroende på sammanlagd information från flera lager. Exempelvis räknas
highway-taggen ut här.

nvdb_ti.py

Översättning av NVDB-tidsintervall till OSM-format. Väldigt hackigt
implementerat och inte heltäckande. Borde egentligen göras mer
generell med en tidsintervall-klass istället för en massa bollande med
strängar som nu. Men i praktiken så funkar detta, det har
kompletterats med fler fall efter hand de dyker upp i datat.

I loggen skrivs det i slutet ut en list av alla tidsintervall som
översatts, titta gärna på den och se så det ser vettigt ut. Om inte
behöver koden kompletteras med ytterligare något fall.

twodimsearch.py:

Datastruktur för olika typer av 2d-sökningar, främst att hitta punkter
som är inom ett visst avstånd. En effektiv datastruktur för detta är
ett kd-träd, men de Python-implementationer jag hittade passade inte
syftet eller var långsamma, så nu används stället ordnade träd, ett
för x och ett för y för varje x.

Att göra en optimal implementation av detta skulle snabba upp skriptet
rejält.

geometry_search.py:

Började som en generell sökstruktur för att hitta korsande linjer och
liknande, men mer specifika NVDB-funktioner har krypit in över
tiden, så den är inte längre så isolerad modul som jag skulle
önska. Från början var det tänkt att all geometri skulle matas in när
den objektet skapas, men pga små-fel i NVDB-datat har en
kompletteringsfunktion behövt läggas till i efterhand, vilket blev
lite hackigt. Men det funkar.

waydb.py:

"Databas" för NVDB-geometrin och funktioner för att sammanfoga ett
NVDB lager i taget. Databasen skapas med lagret DKReflinjetillkomst
som innehåller "all" geometri, detta används därefter som en fast
referensgeometri som de andra lagren anpassas till.

Tyvärr visade det sig att referenslagret ofta inte är 100%
i ordning. Ibland saknas vissa delar av geometrin, vissa linjer är
avhuggna osv. Därför kan geometrin numera kompletteras i
efterhand, med en lite knölig funktion (bygger på att få
kompletteringar behöver göras). Skulle man göra om det från början
skulle man antagligen designa det så att man startar med tom databas
och normalfallet är att geometrin byggs upp lager för lager.

I teorin ska alla NVDB-lager matcha referensgeometrin exakt och
vägsegment som ska sitta ihop ska verkligen sitta ihop i geometrin
osv. I praktiken är det emellertid inte så, så mycket i waydb handlar
om att snäppa punkter till referensgeometrin och få allt att sitta
ihop i slutänden. Waydb använder twodimsearch och geometry_serach till
stor del för att åstadkomma detta.

övriga filer:

Övriga filer är småfiler med hjälpfunktioner och datatyper, tämligen
uppenbart vad de är genom att öppna och titta i dem.


Övriga kommentarer
------------------

Detta avsnitt kan snabbt komma bli utdaterat, se koden. Detta gäller
första release.

I vissa fall har nya taggar som inte ännu används i OSM lagts till. Så
långt som möjligt försker de undvikas.

Här är en lista:

 - hästrastgård => amenity=horse_exercise_area sällsynt tagg för
     rastplatser
 - miljözon-klass 1/2/3 => environmental_zone:sv=1/2/3
 - beskickningsfordon => diplomatic (i samma klass som permit_holder,
     disabled etc)
 - på- eller avstigning => embark_disembark (i samma klass som
     destination, delivery etc)

Tidsintervallen använder inga custom-taggar, men ovanlig notation som
inte har fått mycket användning tidigare i Sverige.

 "vardag utom dag före sön- och helgdag" =>
   Mo-Fr <klockslag>; PH -1 day off; PH off

"PH -1 day" är ovanlig, men finns och betyder "dag för publik helgdag"
(alltså inte dag före vanliga söndagar).

Rondeller har ofta namn. I de kartor som bygger på NVDB-datat så
använder man i regel gatunamn även i rondeller, men skriptet lägger
dit rondellnamnet istället, medan gatunamnen tas bort eftersom
OSM-tradition är att inte ha gatunamn inne i rondeller.
