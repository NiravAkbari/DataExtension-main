# Ignoring warnings
import warnings

from Finale_duplicate_main import add_new_address_column
warnings.filterwarnings("ignore")
import sys

#from abbr import state_abbrev_list

#importing all the required Libraries
""" import html
import pyap
import requests """

import pandas as pd
import numpy as np
import re
from domparser.dom import DOM
import hashlib
import phonenumbers
from address_parser import USAddressParser
from abbr import us_state_to_abbrev
from abbr import state_abbrev_list
from datetime import date
import datetime
from abbr import address_abbrev_street_suffix
#from non_usa_regex import canada_regex, Australia_regex, UK_regex



arguments = sys.argv
today=datetime.datetime.now()

extension='.xlsx'
#input_file='Biznow_Domain_inputHQ_0'
input_file= "input"

if not input_file:
    print("Please give input file (xlsx) name without extension")
    exit() 


output_file="social_link/input_folder/"+input_file+"_2_"+today.strftime("%Y_%m_%dT%H_%M_%S")+extension

excel_data = pd.read_excel(input_file+extension)

df = pd.DataFrame(excel_data)

unique_domains=df['Domain'].unique()


biz_id = df['id'].tolist()
print("The len of ids is:",len(biz_id))


html_addr_dict={
    'Google_Company_Name':[],
    'Company_Website':[],
    'Contact_Page':[],
    'S3 URL':[],
    'Headquarters':[],
    'Headquarters Text':[],  
    
    'Html Address Text':[],
    'Html Snippet':[],
    'Page Type':[],
    'Address Count':[],
    'Address Location':[],  
    'Raw_Address' : [],
    'Address_1' : [],
    "Address_2" : [],
    'City' : [],
    'State' : [],
    'Postal_Code' : [],
    'Country' : [],
    'Company_Phone' : [],
    'Company_Email' : [],
    'Headquarters_snippet': [],
    'phone_no':[],
    'flex_no':[],
    'email_adrress_list':[]
}

""" excel_data = pd.read_excel('Main_zip_code.xlsx')
# Convert to dataframe and specific fields
df = pd.DataFrame(excel_data, columns=['Zips'])
# Return a list
zip_code_list = df['Zips'].tolist()
#print("The len of sample urls is:",len(zip_code_list)) """

# Function(xpath list)
# return Phone, Fax, Email
# Map with xpath each phone, fax and email
# If no xpath search normally and get phone fax email
# Tagging from where we got phone fax email


#biz_s3_link = ['https://rhoaiautomationindias3-datables.s3.amazonaws.com/urlchecker/032023/b2EnDkshZR6LSEqnVvuvMm_OG/c7iMRwnoid9h9gGeeQWbmZ.html']
#biz_s3_link = ['https://rhoaiautomationindias3-datables.s3.amazonaws.com/urlchecker/032023/b2EnDkshZR6LSEqnVvuvMm_OG/8bn8DsZmTL55bVDu4W44Ud.html']
#biz_s3_link = ['https://azahvac.com/hvac-services-in-va-heating-cooling-plumbing-in-virginia-va/hvac-and-air-conditioning-services-in-prince-george-county-va/']
#biz_s3_link = ['https://www.bayareapropertymanagement.com/meet-the-team']
#biz_s3_link = ['https://rhoaiautomationindias3-datables.s3.amazonaws.com/urlchecker/032023/b2EnDkshZR6LSEqnVvuvMm_OG/abZY5CBev6d6HYrr9cJWzo.html']

#list_a=_dom.xpath("//a[re:test(string(),'PA 15\d+')]")

""" pattern = '|'.join([rf'\b{a}\b' for a in streetAbbr])
regex_string = f'{pattern}'
print(regex_string) """

keyword_list_hq = ['Headquarters', 'Headquarter', 'HQ', 'Main Office', 'Central office', 'Head office', 'Corporate office', 'Principal office', 'Administrative center','Home Office','Corporate Headquarters','Corporate']

pattern_hq = re.compile(r'\b({})\b'.format('|'.join(map(re.escape, keyword_list_hq))), re.IGNORECASE)

#Non USA patterns Canada
pattern_canada = r'\b(?:\bAB\b|\bAlberta\b|\bBC\b|\bBritish Columbia\b|\bMB\b|\bManitoba\b|\bNB\b|\bNew Brunswick\b|\bNL\b|\bNewfoundland and Labrador\b|\bNS\b|\bNova Scotia\b|\bNorthwest Territories\b|\bNT\b|\bNunavut\b|\bNU\b|\bON\b|\bOntario\b|\bPE\b|\bPrince Edward Island\b|\bQC\b|\bQuebec\b|\bSK\b|\bSaskatchewan\b|\bYT\b|\bYukon\b)\b\s[A-Z]\d[A-Z]\s\d[A-Z]\d'

states_zip_pattern=r'((?:\bAlabama\b|\bAlaska\b|\bArizona\b|\bArkansas\b|\bCalifornia\b|\bColorado\b|\bConnecticut\b|\bDelaware\b|\bDistrict of Columbia\b|\bFlorida\b|\bGeorgia\b|\bHawaii\b|\bIdaho\b|\bIllinois\b|\bILLionois\b|\bILLionois.|\bIndiana\b|\bIowa\b|\bKansas\b|\bKentucky\b|\bLouisiana\b|\bMaine\b|\bMaryland\b|\bMassachusetts\b|\bMass\b|\bMichigan\b|\bMinnesota\b|\bMississippi\b|\bMissouri\b|\bMontana\b|\bNebraska\b|\bNevada\b|\bNew Hampshire\b|\bNew Jersey\b|\bNew Mexico\b|\bNew York\b|\bNorth Carolina\b|\bNorth Dakota\b|\bOhio\b|\bOklahoma\b|\bOregon\b|\bPennsylvania\b|\bPuerto Rico\b|\bRhode Island\b|\bSouth Carolina\b|\bSouth Dakota\b|\bTennessee\b|\bTexas\b|\bUtah\b|\bVermont\b|\bVirginia\b|\bWashington\b|\bWest Virginia\b|\bWisconsin\b|\bWyoming\b|\bAL\b|\bAK\b|\bAZ\b|\bAR\b|\bCA\b|\bCO\b|\bCT\b|\bDE\b|\bDC\b|\bFL\b|\bGA\b|\bHI\b|\bID\b|\bIL\b|\bIN\b|\bIA\b|\bKS\b|\bKY\b|\bLA\b|\bME\b|\bMD\b|\bMA\b|\bMI\b|\bMN\b|\bMS\b|\bMO\b|\bMT\b|\bNE\b|\bNV\b|\bNH\b|\bNJ\b|\bNM\b|\bNY\b|\bNC\b|\bND\b|\bOH\b|\bOK\b|\bOR\b|\bPA\b|\bPR\b|\bRI\b|\bSC\b|\bSD\b|\bTN\b|\bTX\b|\bUT\b|\bVT\b|\bVA\b|\bWA\b|\bWV\b|\bWI\b|\bWY\b|\bA.L.|\bA.K.|\bA.Z.|\bA.R.|\bC.A.|\bC.O.|\bC.T.|\bD.E.|\bD.C.|\bF.L.|\bG.A.|\bH.I.|\bI.D.|\bI.L.|\bI.N.|\bI.A.|\bK.S.|\bK.Y.|\bL.A.|\bM.E.|\bM.D.|\bM.A.|\bM.I.|\bM.N.|\bM.S.|\bM.O.|\bM.T.|\bN.E.|\bN.V.|\bN.H.|\bN.J.|\bN.M.|\bN.Y.|\bN.C.|\bN.D.|\bO.H.|\bO.K.|\bO.R.|\bP.A.|\bP.R.|\bR.I.|\bS.C.|\bS.D.|\bT.N.|\bT.X.|\bU.T.|\bV.T.|\bV.A.|\bW.A.|\bW.V.|\bW.I.|\bW.Y.)[\—\| ,\-\.\n\– \(]+(?:\d{4,5}))\b(?!\W*.+?(Ste\.|Rd\.|Road|Suite\b|of\b|the\b|1st\b))'

pattern_zipcode = re.compile(fr"{states_zip_pattern}", flags=re.U|re.I|re.M)

def md5_hash(string):
    md5_hash = hashlib.md5()
    md5_hash.update(string.encode('utf-8'))
    return md5_hash.hexdigest()

def treat_raw_html(html_content):
    pattern = r"<!--(.*?)-->"
    # remove all comments from the document using regex
    html_content = re.sub(pattern, "", html_content, flags=re.DOTALL)
    return html_content

def clean_text(input_str):

    input_str = input_str.replace('\n', ' ')
    input_str = re.sub(r'\s{1,}', ' ', input_str)
    input_str=re.sub(r'[^\w\s]', '', input_str)
    return input_str

def get_non_us_pattern(test_address):
    
    pattern_canada = r"\b(?:\bAB\b|\bAlberta\b|\bBC\b|\bBritish Columbia\b|\bMB\b|\bManitoba\b|\bNB\b|\bNew Brunswick\b|\bNL\b|\bNewfoundland and Labrador\b|\bNS\b|\bNova Scotia\b|\bNorthwest Territories\b|\bNT\b|\bNunavut\b|\bNU\b|\bON\b|\bOntario\b|\bPE\b|\bPrince Edward Island\b|\bQC\b|\bQuebec\b|\bSK\b|\bSaskatchewan\b|\bYT\b|\bYukon\b)\b,?\s[A-Z]\d[A-Z]\s\d[A-Z]\d"  
    matches_canada = re.findall(pattern_canada, test_address, re.IGNORECASE)
    
    pattern_AUS = r"\b(?:\bAustralian Capital Territory\b|\bACT\b|\bNew South Wales\b|\bNSW\b|\bNorthern Territory\b|\bNT\b|\bQueensland\b|\bQld\b|\bSouth Australia\b|\bSA\b|\bVictoria\b|\bVic\b|\bTasmania\b|\bTas\b|\bWestern Australia\b|\bWA\b)\b\s\d{4}"
    matches_AUS = re.findall(pattern_AUS, test_address, re.IGNORECASE)
    
    pattern_UK = r"\b(?:\bCAM\b|\bCMA\b|\bDBY\b|\bDEV\b|\bDOR\b|\bESX\b|\bESS\b|\bGLS\b|\bHAM\b|\bHRT\b|\bKEN\b|\bLAN\b|\bLEC\b|\bLIN\b|\bNFK\b|\bNYK\b|\bNTT\b|\bOXF\b|\bSOM\b|\bSTS\b|\bSFK\b|\bSRY\b|\bWAR\b|\bWSX\b|\bWOR\b|\bLND\b|\bBDG\b|\bBNE\b|\bBEX\b|\bBEN\b|\bBRY\b|\bCMD\b|\bCRY\b|\bEAL\b|\bENF\b|\bGRE\b|\bHCK\b|\bHMF\b|\bHRY\b|\bHRW\b|\bHAV\b|\bHIL\b|\bHNS\b|\bISL\b|\bKEC\b|\bKTT\b|\bLBH\b|\bLEW\b|\bMRT\b|\bNWM\b|\bRDB\b|\bRIC\b|\bSWK\b|\bSTN\b|\bTWH\b|\bWFT\b|\bWND\b|\bWSM\b|\bBNS\b|\bBIR\b|\bBOL\b|\bBRD\b|\bBUR\b|\bCLD\b|\bCOV\b|\bDNC\b|\bDUD\b|\bGAT\b|\bKIR\b|\bKWL\b|\bLDS\b|\bLIV\b|\bMAN\b|\bNET\b|\bNTY\b|\bOLD\b|\bRCH\b|\bROT\b|\bSHN\b|\bSLF\b|\bSAW\b|\bSFT\b|\bSHF\b|\bSOL\b|\bSTY\b|\bSKP\b|\bSND\b|\bTAM\b|\bTRF\b|\bWKF\b|\bWLL\b|\bWGN\b|\bWRL\b|\bWLV\b|\bBAS\b|\bBDF\b|\bBBD\b|\bBPL\b|\bBCP\b|\bBRC\b|\bBNH\b|\bBST\b|\bBKM\b|\bCBF\b|\bCHE\b|\bCHW\b|\bCON\b|\bDAL\b|\bDER\b|\bDUR\b|\bERY\b|\bHAL\b|\bHPL\b|\bHEF\b|\bIOW\b|\bIOS\b|\bKHL\b|\bLCE\b|\bLUT\b|\bMDW\b|\bMDB\b|\bMIK\b|\bNEL\b|\bNLN\b|\bNNH\b|\bNSM\b|\bNBL\b|\bNGM\b|\bPTE\b|\bPLY\b|\bPOR\b|\bRDG\b|\bRCC\b|\bRUT\b|\bSHR\b|\bSLG\b|\bSGC\b|\bSTH\b|\bSOS\b|\bSTT\b|\bSTE\b|\bSWD\b|\bTFW\b|\bTHR\b|\bTOB\b|\bWRT\b|\bWBK\b|\bWNH\b|\bWIL\b|\bWNM\b|\bWOK\b|\bYOR\b|\bANN\b|\bAND\b|\bABC\b|\bBFS\b|\bCCG\b|\bDRS\b|\bFMO\b|\bLBC\b|\bMEA\b|\bMUL\b|\bNMD\b|\bABE\b|\bABD\b|\bANS\b|\bAGB\b|\bCLK\b|\bDGY\b|\bDND\b|\bEAY\b|\bEDU\b|\bELN\b|\bERW\b|\bEDH\b|\bELS\b|\bFAL\b|\bFIF\b|\bGLG\b|\bHLD\b|\bIVC\b|\bMLN\b|\bMRY\b|\bNAY\b|\bNLK\b|\bORK\b|\bPKN\b|\bRFW\b|\bSCB\b|\bZET\b|\bSAY\b|\bSLK\b|\bSTG\b|\bWDU\b|\bWLN\b|\bBGW\b|\bBGE\b|\bCAY\b|\bCRF\b|\bCMN\b|\bCGN\b|\bCWY\b|\bDEN\b|\bFLN\b|\bGWN\b|\bAGY\b|\bMTY\b|\bMON\b|\bNTL\b|\bNWP\b|\bPEM\b|\bPOW\b|\bRCT\b|\bSWA\b|\bTOF\b|\bVGL\b|\bWRX\b|\bCambridgeshire\b|\bCumbria\b|\bDerbyshire\b|\bDevon\b|\bDorset\b|\bEast Sussex\b|\bEssex\b|\bGloucestershire\b|\bHampshire\b|\bHertfordshire\b|\bKent\b|\bLancashire\b|\bLeicestershire\b|\bLincolnshire\b|\bNorfolk\b|\bNorth Yorkshire\b|\bNottinghamshire\b|\bOxfordshire\b|\bSomerset\b|\bStaffordshire\b|\bSuffolk\b|\bSurrey\b|\bWarwickshire\b|\bWest Sussex\b|\bWorcestershire\b|\bLondon\b|\bBarking and Dagenham\b|\bBarnet\b|\bBexley\b|\bBrent\b|\bBromley\b|\bCamden\b|\bCroydon\b|\bEaling\b|\bEnfield\b|\bGreenwich\b|\bHackney\b|\bHammersmith and Fulham\b|\bHaringey\b|\bHarrow\b|\bHavering\b|\bHillingdon\b|\bHounslow\b|\bIslington\b|\bKensington and Chelsea\b|\bKingston upon Thames\b|\bLambeth\b|\bLewisham\b|\bMerton\b|\bNewham\b|\bRedbridge\b|\bRichmond upon Thames\b|\bSouthwark\b|\bSutton\b|\bTower Hamlets\b|\bWaltham Forest\b|\bWandsworth\b|\bWestminster\b|\bBarnsley\b|\bBirmingham\b|\bBolton\b|\bBradford\b|\bBury\b|\bCalderdale\b|\bCoventry\b|\bDoncaster\b|\bDudley\b|\bGateshead\b|\bKirklees\b|\bKnowsley\b|\bLeeds\b|\bLiverpool\b|\bManchester\b|\bNewcastle upon Tyne\b|\bNorth Tyneside\b|\bOldham\b|\bRochdale\b|\bRotherham\b|\bSt. Helens\b|\bSalford\b|\bSandwell\b|\bSefton\b|\bSheffield\b|\bSolihull\b|\bSouth Tyneside\b|\bStockport\b|\bSunderland\b|\bTameside\b|\bTrafford\b|\bWakefield\b|\bWalsall\b|\bWigan\b|\bWirral\b|\bWolverhampton\b|\bBath and North East Somerset\b|\bBedford\b|\bBlackburn with Darwen\b|\bBlackpool\b|\bBournemouth\b|\bBournemouth, Christchurch and Poole\b|\bBracknell Forest\b|\bBrighton and Hove\b|\bBristol, City of\b|\bBuckinghamshire\b|\bCentral Bedfordshire\b|\bCheshire East\b|\bCheshire West and Chester\b|\bCornwall\b|\bDarlington\b|\bDerby\b|\bDurham, County\b|\bEast Riding of Yorkshire\b|\bHalton\b|\bHartlepool\b|\bHerefordshire\b|\bIsle of Wight\b|\bIsles of Scilly\b|\bKingston upon Hull\b|\bLeicester\b|\bLuton\b|\bMedway\b|\bMiddlesbrough\b|\bMilton Keynes\b|\bNorth East Lincolnshire\b|\bNorth Lincolnshire\b|\bNorth Northamptonshire\b|\bNorth Somerset\b|\bNorthumberland\b|\bNottingham\b|\bPeterborough\b|\bPlymouth\b|\bPortsmouth\b|\bReading\b|\bRedcar and Cleveland\b|\bRutland\b|\bShropshire\b|\bSlough\b|\bSouth Gloucestershire\b|\bSouthampton\b|\bSouthend-on-Sea\b|\bStockton-on-Tees\b|\bStoke-on-Trent\b|\bSwindon\b|\bTelford and Wrekin\b|\bThurrock\b|\bTorbay\b|\bWarrington\b|\bWest Berkshire\b|\bWest Northamptonshire\b|\bWiltshire\b|\bWindsor and Maidenhead\b|\bWokingham\b|\bYork\b|\bAntrim and Newtownabbey\b|\bArds and North Down\b|\bArmagh City, Banbridge and Craigavon\b|\bBelfast City\b|\bCauseway Coast and Glens\b|\bDerry and Strabane\b|\bFermanagh and Omagh\b|\bLisburn and Castlereagh\b|\bMid and East Antrim\b|\bMid-Ulster\b|\bNewry, Mourne and Down\b|\bAberdeen City\b|\bAberdeenshire\b|\bAngus\b|\bArgyll and Bute\b|\bClackmannanshire\b|\bDumfries and Galloway\b|\bDundee City\b|\bEast Ayrshire\b|\bEast Dunbartonshire\b|\bEast Lothian\b|\bEast Renfrewshire\b|\bEdinburgh, City of\b|\bEilean Siar\b|\bFalkirk\b|\bFife\b|\bGlasgow City\b|\bHighland\b|\bInverclyde\b|\bMidlothian\b|\bMoray\b|\bNorth Ayrshire\b|\bNorth Lanarkshire\b|\bOrkney Islands\b|\bPerth and Kinross\b|\bRenfrewshire\b|\bScottish Borders\b|\bShetland Islands\b|\bSouth Ayrshire\b|\bSouth Lanarkshire\b|\bStirling\b|\bWest Dunbartonshire\b|\bWest Lothian\b|\bBlaenau Gwent\b|\bBridgend\b|\bCaerphilly\b|\bCardiff\b|\bCarmarthenshire\b|\bCeredigion\b|\bConwy\b|\bDenbighshire\b|\bFlintshire\b|\bGwynedd\b|\bIsle of Anglesey\b|\bMerthyr Tydfil\b|\bMonmouthshire\b|\bNeath Port Talbot\b|\bNewport\b|\bPembrokeshire\b|\bPowys\b|\bRhondda Cynon Taff\b|\bSwansea\b|\bTorfaen\b|\bVale of Glamorgan\b|\bWrexham\b|\bCAM\b|\bCMA\b|\bDBY\b|\bDEV\b|\bDOR\b|\bESX\b|\bESS\b|\bGLS\b|\bHAM\b|\bHRT\b|\bKEN\b|\bLAN\b|\bLEC\b|\bLIN\b|\bNFK\b|\bNYK\b|\bNTT\b|\bOXF\b|\bSOM\b|\bSTS\b|\bSFK\b|\bSRY\b|\bWAR\b|\bWSX\b|\bWOR\b|\bLND\b|\bBDG\b|\bBNE\b|\bBEX\b|\bBEN\b|\bBRY\b|\bCMD\b|\bCRY\b|\bEAL\b|\bENF\b|\bGRE\b|\bHCK\b|\bHMF\b|\bHRY\b|\bHRW\b|\bHAV\b|\bHIL\b|\bHNS\b|\bISL\b|\bKEC\b|\bKTT\b|\bLBH\b|\bLEW\b|\bMRT\b|\bNWM\b|\bRDB\b|\bRIC\b|\bSWK\b|\bSTN\b|\bTWH\b|\bWFT\b|\bWND\b|\bWSM\b|\bBNS\b|\bBIR\b|\bBOL\b|\bBRD\b|\bBUR\b|\bCLD\b|\bCOV\b|\bDNC\b|\bDUD\b|\bGAT\b|\bKIR\b|\bKWL\b|\bLDS\b|\bLIV\b|\bMAN\b|\bNET\b|\bNTY\b|\bOLD\b|\bRCH\b|\bROT\b|\bSHN\b|\bSLF\b|\bSAW\b|\bSFT\b|\bSHF\b|\bSOL\b|\bSTY\b|\bSKP\b|\bSND\b|\bTAM\b|\bTRF\b|\bWKF\b|\bWLL\b|\bWGN\b|\bWRL\b|\bWLV\b|\bBAS\b|\bBDF\b|\bBBD\b|\bBPL\b|\bBCP\b|\bBRC\b|\bBNH\b|\bBST\b|\bBKM\b|\bCBF\b|\bCHE\b|\bCHW\b|\bCON\b|\bDAL\b|\bDER\b|\bDUR\b|\bERY\b|\bHAL\b|\bHPL\b|\bHEF\b|\bIOW\b|\bIOS\b|\bKHL\b|\bLCE\b|\bLUT\b|\bMDW\b|\bMDB\b|\bMIK\b|\bNEL\b|\bNLN\b|\bNNH\b|\bNSM\b|\bNBL\b|\bNGM\b|\bPTE\b|\bPLY\b|\bPOR\b|\bRDG\b|\bRCC\b|\bRUT\b|\bSHR\b|\bSLG\b|\bSGC\b|\bSTH\b|\bSOS\b|\bSTT\b|\bSTE\b|\bSWD\b|\bTFW\b|\bTHR\b|\bTOB\b|\bWRT\b|\bWBK\b|\bWNH\b|\bWIL\b|\bWNM\b|\bWOK\b|\bYOR\b|\bANN\b|\bAND\b|\bABC\b|\bBFS\b|\bCCG\b|\bDRS\b|\bFMO\b|\bLBC\b|\bMEA\b|\bMUL\b|\bNMD\b|\bABE\b|\bABD\b|\bANS\b|\bAGB\b|\bCLK\b|\bDGY\b|\bDND\b|\bEAY\b|\bEDU\b|\bELN\b|\bERW\b|\bEDH\b|\bELS\b|\bFAL\b|\bFIF\b|\bGLG\b|\bHLD\b|\bIVC\b|\bMLN\b|\bMRY\b|\bNAY\b|\bNLK\b|\bORK\b|\bPKN\b|\bRFW\b|\bSCB\b|\bZET\b|\bSAY\b|\bSLK\b|\bSTG\b|\bWDU\b|\bWLN\b|\bBGW\b|\bBGE\b|\bCAY\b|\bCRF\b|\bCMN\b|\bCGN\b|\bCWY\b|\bDEN\b|\bFLN\b|\bGWN\b|\bAGY\b|\bMTY\b|\bMON\b|\bNTL\b|\bNWP\b|\bPEM\b|\bPOW\b|\bRCT\b|\bSWA\b|\bTOF\b|\bVGL\b|\bWRX\b|\bCambridgeshire\b|\bCumbria\b|\bDerbyshire\b|\bDevon\b|\bDorset\b|\bEast Sussex\b|\bEssex\b|\bGloucestershire\b|\bHampshire\b|\bHertfordshire\b|\bKent\b|\bLancashire\b|\bLeicestershire\b|\bLincolnshire\b|\bNorfolk\b|\bNorth Yorkshire\b|\bNottinghamshire\b|\bOxfordshire\b|\bSomerset\b|\bStaffordshire\b|\bSuffolk\b|\bSurrey\b|\bWarwickshire\b|\bWest Sussex\b|\bWorcestershire\b|\bLondon\b|\bBarking and Dagenham\b|\bBarnet\b|\bBexley\b|\bBrent\b|\bBromley\b|\bCamden\b|\bCroydon\b|\bEaling\b|\bEnfield\b|\bGreenwich\b|\bHackney\b|\bHammersmith and Fulham\b|\bHaringey\b|\bHarrow\b|\bHavering\b|\bHillingdon\b|\bHounslow\b|\bIslington\b|\bKensington and Chelsea\b|\bKingston upon Thames\b|\bLambeth\b|\bLewisham\b|\bMerton\b|\bNewham\b|\bRedbridge\b|\bRichmond upon Thames\b|\bSouthwark\b|\bSutton\b|\bTower Hamlets\b|\bWaltham Forest\b|\bWandsworth\b|\bWestminster\b|\bBarnsley\b|\bBirmingham\b|\bBolton\b|\bBradford\b|\bBury\b|\bCalderdale\b|\bCoventry\b|\bDoncaster\b|\bDudley\b|\bGateshead\b|\bKirklees\b|\bKnowsley\b|\bLeeds\b|\bLiverpool\b|\bManchester\b|\bNewcastle upon Tyne\b|\bNorth Tyneside\b|\bOldham\b|\bRochdale\b|\bRotherham\b|\bSt. Helens\b|\bSalford\b|\bSandwell\b|\bSefton\b|\bSheffield\b|\bSolihull\b|\bSouth Tyneside\b|\bStockport\b|\bSunderland\b|\bTameside\b|\bTrafford\b|\bWakefield\b|\bWalsall\b|\bWigan\b|\bWirral\b|\bWolverhampton\b|\bBath and North East Somerset\b|\bBedford\b|\bBlackburn with Darwen\b|\bBlackpool\b|\bBournemouth, Christchurch and Poole\b|\bBracknell Forest\b|\bBrighton and Hove\b|\bBristol, City of\b|\bBuckinghamshire\b|\bCentral Bedfordshire\b|\bCheshire East\b|\bCheshire West and Chester\b|\bCornwall\b|\bDarlington\b|\bDerby\b|\bDurham, County\b|\bEast Riding of Yorkshire\b|\bHalton\b|\bHartlepool\b|\bHerefordshire\b|\bIsle of Wight\b|\bIsles of Scilly\b|\bKingston upon Hull\b|\bLeicester\b|\bLuton\b|\bMedway\b|\bMiddlesbrough\b|\bMilton Keynes\b|\bNorth East Lincolnshire\b|\bNorth Lincolnshire\b|\bNorth Northamptonshire\b|\bNorth Somerset\b|\bNorthumberland\b|\bNottingham\b|\bPeterborough\b|\bPlymouth\b|\bPortsmouth\b|\bReading\b|\bRedcar and Cleveland\b|\bRutland\b|\bShropshire\b|\bSlough\b|\bSouth Gloucestershire\b|\bSouthampton\b|\bSouthend-on-Sea\b|\bStockton-on-Tees\b|\bStoke-on-Trent\b|\bSwindon\b|\bTelford and Wrekin\b|\bThurrock\b|\bTorbay\b|\bWarrington\b|\bWest Berkshire\b|\bWest Northamptonshire\b|\bWiltshire\b|\bWindsor and Maidenhead\b|\bWokingham\b|\bYork\b|\bAntrim and Newtownabbey\b|\bArds and North Down\b|\bArmagh City, Banbridge and Craigavon\b|\bBelfast City\b|\bCauseway Coast and Glens\b|\bDerry and Strabane\b|\bFermanagh and Omagh\b|\bLisburn and Castlereagh\b|\bMid and East Antrim\b|\bMid-Ulster\b|\bNewry, Mourne and Down\b|\bAberdeen City\b|\bAberdeenshire\b|\bAngus\b|\bArgyll and Bute\b|\bClackmannanshire\b|\bDumfries and Galloway\b|\bDundee City\b|\bEast Ayrshire\b|\bEast Dunbartonshire\b|\bEast Lothian\b|\bEast Renfrewshire\b|\bEdinburgh, City of\b|\bEilean Siar\b|\bFalkirk\b|\bFife\b|\bGlasgow City\b|\bHighland\b|\bInverclyde\b|\bMidlothian\b|\bMoray\b|\bNorth Ayrshire\b|\bNorth Lanarkshire\b|\bOrkney Islands\b|\bPerth and Kinross\b|\bRenfrewshire\b|\bScottish Borders\b|\bShetland Islands\b|\bSouth Ayrshire\b|\bSouth Lanarkshire\b|\bStirling\b|\bWest Dunbartonshire\b|\bWest Lothian\b|\bBlaenau Gwent\b|\bBridgend\b|\bCaerphilly\b|\bCardiff\b|\bCarmarthenshire\b|\bCeredigion\b|\bConwy\b|\bDenbighshire\b|\bFlintshire\b|\bGwynedd\b|\bIsle of Anglesey\b|\bMerthyr Tydfil\b|\bMonmouthshire\b|\bNeath Port Talbot\b|\bNewport\b|\bPembrokeshire\b|\bPowys\b|\bRhondda Cynon Taff\b|\bSwansea\b|\bTorfaen\b|\bVale of Glamorgan\b|\bWrexham\b)\b,?\s(?:[A-Z][A-Z]\d\s\d[A-Z][A-Z]|[A-Z][A-Z]\d\d\s\d[A-Z][A-Z]|[A-Z]\d\d\s\d[A-Z][A-Z]|[A-Z]\d\s\d[A-Z][A-Z]|[A-Z]\d[A-Z]\s\d[A-Z][A-Z]|[A-Z][A-Z]\d[A-Z]\s\d[A-Z][A-Z])"
    matches_UK = re.findall(pattern_UK, test_address)
    
    if matches_canada:
        print("Got Canada Match:",matches_canada)
        return matches_canada
    
    elif matches_UK:
        print("Got UK Match:",matches_UK)
        return matches_UK
            
    elif matches_AUS:
        print("Got Australia Match:",matches_AUS)
        return matches_AUS

def get_text_to_search(text_content):
    #html_content=treat_raw_html(html_content)
    all_searches=[]
    exclude_words = ['fall', 'in']
        
    matches = pattern_zipcode.findall(text_content)
    if matches:
        print("Current_match:",matches)
        for match in matches:
            searched_str=match[0]
            #searched_str=match
            #if searched_str.lower() !=  "in " +"".join(str(x) for x in re.findall( r'\b\d{4}\b', searched_str)):               
            all_searches.append(searched_str)
    
        all_searches = [item for item in all_searches if not any((item.lower().startswith(word) and item[len(word):].strip().isdigit() and len(item[len(word):].strip()) == 4) for word in exclude_words)]

       

        """ has_five_digit_item = any(item.endswith(('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')) and len(item) == 5 for item in all_searches)
        if has_five_digit_item:
            all_searches = [item for item in all_searches if not (item.endswith(('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')) and len(item) == 4)] """


            #print("USA:",all_searches)
                
    #Also searching for non us Address
    # can_aus_uk = get_non_us_pattern(text_content)
    # for non_usa in can_aus_uk:
    #     all_searches.append(non_usa)
    #     print("Got Non USA")

    
    # if not all_searches:
    #     for line in text_content.split("\n"):
    #         data = [line  for i in State_names if i in line]
    #         if data:
    #             data =  list(set(data))
    #             for x in data:
    #                 finale_data = list(set([x for z in x.split() if z in State_names]))
    #                 if finale_data:
    #                     all_searches.append("".join(str(x) for x in finale_data))
    #                 else:
    #                     finale_data = list(set([x for z in x.split(",") if z.strip() in State_names]))
    #                     if finale_data:
    #                         all_searches.append("".join(str(x) for x in finale_data))
    #         else:
    #             Contry_name = ['United States',"USA","usa","united states"]
    #             data = [line  for i in Contry_name if i in line]
    #             if data:
    #                 data =  list(set(data))
    #                 for x in data:
    #                     finale_data = list(set([x for z in x.split() if z in Contry_name]))
    #                     if finale_data:
    #                         all_searches.append("".join(str(x) for x in finale_data))
    #                     else:
    #                         finale_data = list(set([x for z in x.split(",") if z.strip() in Contry_name]))
    #                         if finale_data:
    #                             all_searches.append("".join(str(x) for x in finale_data))

    
    
    all_searches_list = [' '.join(item.replace('\n', ' ').split()) for item in all_searches]
    all_searches_list = [' '.join(item.split()) for item in all_searches_list]

   
    return all_searches_list
    

def append_to_pd(domain_rows,contact_url,address_snippet,address_snippet_text,page_type,Domain,hq_snippet,count='NA',location='',hq_text='',headquarters='',addressData={},phone_no="",flex_no="",email_adrress_list=""):
    id = ""
    s3_url = ""
    forageai_companyid = ""
    companyname = ""
    Domain = ""
    if str(type(domain_rows)) != "<class 'numpy.int64'>":
        s3_url=domain_rows.loc[domain_rows['teampage_urls']==contact_url, 's3_html_link'].values[0]
        forageai_companyid=domain_rows.loc[domain_rows['teampage_urls']==contact_url, 'forageai_companyid'].values[0]
        companyname=domain_rows.loc[domain_rows['teampage_urls']==contact_url, 'companyname'].values[0]

        Domain=domain_rows.loc[domain_rows['teampage_urls']==contact_url, 'Domain'].values[0]
        id=domain_rows.loc[domain_rows['teampage_urls']==contact_url, 'id'].values[0]
    
    html_addr_dict["Google_Company_Name"].append(companyname)
    html_addr_dict["Company_Website"].append(Domain)
    html_addr_dict["Contact_Page"].append(contact_url)
    html_addr_dict["S3 URL"].append(s3_url)
    html_addr_dict['Headquarters'].append(headquarters)
    html_addr_dict['Headquarters Text'].append(hq_text)
                
    html_addr_dict["Html Snippet"].append(address_snippet)
    html_addr_dict["Html Address Text"].append(address_snippet_text)
    html_addr_dict["Page Type"].append(page_type)
    
    html_addr_dict["Address Count"].append(count)
    html_addr_dict["Address Location"].append(location)
    
    address_line_1 = addressData['address_line_1'] if "address_line_1" in addressData and addressData['address_line_1']  else  ""
    address_line_2 = addressData['address_line_2'] if "address_line_2" in addressData  and addressData['address_line_2'] else  "" 
    city = addressData['city'] if "city" in addressData and addressData['city']  else  ""
    postal_code = addressData['postal_code'] if "postal_code" in addressData  and addressData['postal_code'] else  "" 
    raw_address_str = addressData['raw_address_str'] if "raw_address_str" in addressData  and addressData['raw_address_str']  else  "" 
    state = addressData['state'] if 'state' in addressData and addressData['state'] else ""
    try:
        state_tmp = state.replace(".", "")
        state_tmp = state_tmp.replace("\n", "")
        full_state_name = (list(us_state_to_abbrev.keys())[list(us_state_to_abbrev.values()).index(state_tmp.upper())] if len(state_tmp) == 2 else addressData['state']) if state_tmp else ""
    except:
        #state = addressData['state'] if 'state' in addressData and addressData['state'] else ""
        full_state_name=state

    html_addr_dict["Raw_Address"] .append( raw_address_str) 
    html_addr_dict["Address_1"].append(address_line_1)
    html_addr_dict["Address_2"] .append(address_line_2) 
    html_addr_dict["City"] .append(city) 
    html_addr_dict["State"] .append(full_state_name)
    html_addr_dict["Postal_Code"] .append(postal_code)
    
    html_addr_dict['Country'].append('')
    html_addr_dict['Company_Phone'].append('')
    html_addr_dict['Company_Email'].append('')
    #html_addr_dict["Headquarters_snippet"].append(hq_snippet)
    html_addr_dict["Headquarters_snippet"].append("")
    html_addr_dict['phone_no'].append(phone_no)
    html_addr_dict['flex_no'].append(flex_no)
    html_addr_dict['email_adrress_list'].append(email_adrress_list)

    address_ID=''
    if address_line_1.strip():
        address_ID=str(forageai_companyid)+"_"+str(re.sub(r'\W+', '_', address_line_1).lower().strip())
    elif raw_address_str.strip():
        address_ID=str(forageai_companyid)+"_"+str(re.sub(r'\W+', '_', raw_address_str).lower().strip())
    
    if address_ID:
        md5_hash(address_ID)
        
   

    

def get_remaining_address_length(text_address,search_txt):
    text_address=clean_text(text_address)
    search_txt=clean_text(search_txt)
    if len(text_address) and len(search_txt) != 0:
        rest_part_address = text_address.split(search_txt)[0]
        return len(rest_part_address.split())
    else:
        return 0

def check_address_string(input_string,skip_first_check=True):
    #address_abbrev_street_suffix = {'Aly.': 'Alley', 'Aly': 'Alley', 'ALY': 'Alley', 'Anx.': 'Annex'}
    print("address str",input_string)
    print("length address str",len(input_string.split()))

    #exit()
    #This fix is done to handle the case "2001 Old Westfield Road, P.O. Box 1722, Pilot Mountain, NC 27041" where 'Pilot Mountain, NC 27041' comes in a tag
    if skip_first_check==True:
        if len(input_string.split())<5: 
            return 0
        
    
    for key, value in address_abbrev_street_suffix.items():
        pattern = r'\b{}\b'.format(re.escape(key))
        if re.search(pattern, input_string, re.IGNORECASE):
            if not input_string.lower().startswith(key.lower()):
                return 1
        
        pattern = r'\b{}\b'.format(re.escape(value))
        if re.search(pattern, input_string, re.IGNORECASE):
            if not input_string.lower().startswith(value.lower()):
                return 1
            #return 1    
        
    return 0


def check_head_keyword(input_string):
    input_string = re.sub(r"\n", " ", input_string)
    input_string = re.sub(r"\s+", " ", input_string)
    
    
    
    for keyword in keyword_list_hq:
        pattern = r'\b{}\b'.format(re.escape(keyword))
        if re.search(pattern, input_string, re.IGNORECASE|re.DOTALL):
            print("Find")
            return 1
    return 0

def if_in_skip_list(input_string):
    input_string = re.sub(r"\n", " ", input_string)
    input_string = re.sub(r"\s+", " ", input_string)
    
    keyword_list = ['Call us','Phone','Telephone','Email']
    
    for keyword in keyword_list:
        pattern = r'\b{}\b'.format(re.escape(keyword))
        if re.search(pattern, input_string, re.IGNORECASE|re.DOTALL):
            return 1
    return 0

def check_same_start_word(string1, string2):
    # Split strings into words
    words1 = string1.split()
    words2 = string2.split()
    
    # Check if both strings have at least one word
    if len(words1) > 0 and len(words2) > 0:
        # Compare the first word of each string
        if words1[0] == words2[0]:
            return True
    
    return False

def get_address_snippet(_dom, base_xpath):
    
    default_xpath = _dom.xpath(base_xpath)[0]
    text_address = _dom.all_text(default_xpath)
    check = check_address_string(text_address)
    print(check)
    if check == 1:
        return default_xpath
    elm = _dom.xpath(base_xpath)[0]
    counter = 0  # Counter variable
    
    #while elm.getparent() is not None and elm.getparent().tag not in ['html', 'body'] and counter < 4:
    while elm.getparent() is not None and elm.getparent().tag not in ['html', 'body'] and counter < 6:
        elm = elm.getparent()
        text_address = _dom.all_text(elm)
        check = check_address_string(text_address)
        
        if check == 1:
            print(check)
            print("While loop return")
            return elm
        counter += 1  # Increment counter after each iteration
    return default_xpath
    
    
    
def check_headq_parent(_dom, default_element):

    hq_text = _dom.all_text(default_element)
    print("hq_text",hq_text)
    check_hq = check_head_keyword(hq_text)
    
    if check_hq == 1:
        print("Default Return")
        return default_element
    
    
    #elm = _dom.xpath(base_xpath)[0]
    elm = default_element
    counter = 0  # Counter variable
    
    hq_text_child = _dom.all_text(elm)
 
    while elm.getparent() is not None and elm.getparent().tag not in ['html', 'body']:
        
        elm = elm.getparent()
        #print(elm.getparent())
        hq_text_parent = _dom.all_text(elm)
        #print("PARENT",hq_text_parent)
        #print("CHILD",hq_text_child)
        """ search_strings=get_text_to_search(hq_text_parent)
        print("searchStrings",search_strings)
        print("len",len(search_strings)) """
        
        rest_part_address = get_remaining_address_length(hq_text_parent,hq_text_child)
        #hq_text_child = hq_text_parent
        print("rest_part_address",rest_part_address)
        if rest_part_address > 0:
            print("In if cond",rest_part_address)
            print("hq_text_parent",hq_text_parent)
            check_hq = check_head_keyword(hq_text_parent)
            if check_hq == 1:
                return elm
            else:
                counter +=1               
                if if_in_skip_list(hq_text_parent) and counter<2:
                    pass
                else:
                    break
                #pass
            
    return default_element    
            
def get_addresses_list(_dom,search_texts):
    addresses=[]
    addresses_xpath=[]
    base_xpaths=[]
    addressCount=0
    for search_txt in search_texts:
        xpaths=_dom.get_xpath_by_partial_text(search_txt)
        base_xpaths.append(xpaths)
    
    
    xpath_list_str = '|'.join(['|'.join(sublist) for sublist in base_xpaths])
    el=_dom.xpath(xpath_list_str)
    xpath_list_ordered=[e._xpath_str() for e in el ]

    #xpath_list_name_ordered=[e.text for e in el ]
    """ print(xpath_list_name_ordered)

    print(base_xpaths)
    print(xpath_list_str)
    print(xpath_list_ordered)
    exit() """
    for base_xpath in xpath_list_ordered:
        
        try:
            address_snippet_element=get_address_snippet(_dom,base_xpath)
            #print("address_snippet_element:",address_snippet_element)
            #exit()
            if address_snippet_element not in addresses:
                addresses.append(address_snippet_element)
                addresses_xpath.append(base_xpath)
                addressCount +=1
        except IndexError:
            print("\n\n\n\n\nError: Index out of range.\n\n\n\n\n\n")
    return addresses,addresses_xpath

def categorise_urls(url_list,domain):
    list_url_category={}
    list_url_category['CONTACT_URL']=''
    list_url_category['ABOUT_URL']=''
    list_url_category['HOME_URL']=''
    list_url_category['OTHER_URL']=''
    list_url_category['DOMAIN']=domain

    pattern_ignore= re.compile(r'(listing|properties|for-sale|sale|property)', re.IGNORECASE)
    pattern_contact = re.compile(r'contact', re.IGNORECASE) 
    pattern_about= re.compile(r'about', re.IGNORECASE)

    for url in url_list:
        org_url=url
        print(url,"url is >>>>>>>>>>>>>>")
        url = url[len("http://"):] if url.startswith("http://") else url
        url = url[len("https://"):] if url.startswith("https://") else url
        path_parts = [part for i, part in enumerate(url.split("/")) if i > 0 and part != ""]
        print(path_parts)
        if len(path_parts) >0:           

            if path_parts[0].startswith("#"):
                list_url_category['OTHER_URL']=org_url
            else:
                for element in path_parts:                          
                    if pattern_contact.search(element):
                        list_url_category['CONTACT_URL']=org_url
                        #break
                for element in path_parts:                          
                    if pattern_about.search(element):
                        list_url_category['ABOUT_URL']=org_url
                        #break
        else:
            list_url_category['HOME_URL']=org_url
    for url in url_list:
        if url not in list_url_category and not pattern_ignore.search(url):
            list_url_category['OTHER_URL']=url   
    if list_url_category['HOME_URL']==list_url_category['OTHER_URL']:
        list_url_category['OTHER_URL']=''
        
    if not list_url_category['CONTACT_URL'] and not list_url_category['ABOUT_URL'] and not list_url_category['HOME_URL'] and not list_url_category['OTHER_URL']:
        
        list_url_category['OTHER_URL'] = url_list[0]
                     
    return list_url_category
   
def identity_footer(xpath):

    if "/footer" in xpath:
        return "Footer"
    else:
        return "Not Known"
    

def find_email_addresses(text):
    email_domian_name = ['teamtarter','gmail','yahoo','hotmail','aol','msn','live','rediffmail','ymail','googlemail','bigpond','rocketmail','facebook','mail','ntlworld','juno']
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    matches = re.findall(pattern, text) 
    email = []
    if matches:
        email = [data for data in matches]
        # email = [data for data in matches if data.split("@")[-1].split(".")[0] in email_domian_name]
    return list(set(email))
    
def extract_usa_phone_numbers_and_check_is_us_phone_number(text):
    phone_numbers = []
    country_name_list = ["US"]
    for country_name in country_name_list:        
        for match in phonenumbers.PhoneNumberMatcher(text, country_name):
            try:
                phone_number = match.raw_string
                parsed_number = phonenumbers.parse(phone_number, country_name)
                if phonenumbers.is_valid_number(parsed_number) and phonenumbers.region_code_for_number(parsed_number) == country_name:
                    phone_number = re.split(r'[a-z]+',phone_number.lower())[0]
                    phone_numbers.append(phone_number.replace("-","").replace(",","").replace(".","").replace(" ","").replace("(","").replace(")",""))
            except phonenumbers.phonenumberutil.NumberParseException:
                pass
    return list(set(phone_numbers))


def extract_phone_number(text):
    text = str(text)
    fax_number = []
    phone_number = []
    fax_pattern = r'(Fax|F|FAX Number|FAX|fax|f)\s*:?\s*([\d().\s-]+)'
    fax_match = re.search(fax_pattern, text.replace('\n', ' '))
    if fax_match:
        fax_number.append(fax_match.group(2))
    after_fax_number = re.findall(r'([\d().\s-]+)\s*:?\s*(Fax|F|FAX Number|FAX|fax|f)', text)
    if after_fax_number:
        after_fax_number = ["".join(item) for item in after_fax_number]
        after_fax_number = " ".join(after_fax_number)
        pattern = r'\b\d{3}\.\d{3}\.\d{4}\b'
        phone_numbers = re.findall(pattern, after_fax_number)  
        for phoneno in phone_numbers:
            fax_number.append(phoneno)
    phone_number = extract_usa_phone_numbers_and_check_is_us_phone_number(text)
    for data in  fax_number:
        if type(data) == tuple:
            data = list(set(data))[-1]
        data = re.sub(r'\W', '', data)
        phone_number = [x for x in phone_number if re.sub(r'\W', '', x) != data]
    return phone_number, fax_number


def format_phone_numbers(text):
    phone_number_list = ""
    fax_number_list = ""

    phone_number = extract_phone_number(str(text))[0]
    fax_number = extract_phone_number(str(text))[1]

    if phone_number:
        phone_number_list = "___".join(str(x) for x in list(set(phone_number)))
        phone_number_list = "___".join(str(x) for x in extract_usa_phone_numbers_and_check_is_us_phone_number(phone_number_list))

    if fax_number:
        fax_number_list = "___".join(str(x) for x in list(set(fax_number)))
        fax_number_list = "___".join(str(x) for x in extract_usa_phone_numbers_and_check_is_us_phone_number(fax_number_list))

    if not phone_number and not fax_number:
        phone_number_list = "___".join(str(x) for x in list(set(extract_usa_phone_numbers_and_check_is_us_phone_number(text))))

    return phone_number_list, fax_number_list
    


def get_all_ids_and_classes(_dom,element_xpath):
    elm=_dom.xpath(element_xpath)[0]
    attr_ids_classes = []
    while elm.getparent() is not None and elm.getparent().tag not in ['html', 'body']:
        #parents.insert(0, elm.getparent())                    
        elm = elm.getparent()
        id_attr = elm.get('id')
        try:
            attr_ids_classes.extend(id_attr.split())
        except:
            pass

        class_attr = elm.get('class')
        try:
            attr_ids_classes.extend(class_attr.split())
        except:
            pass
        
    return set(attr_ids_classes)
    
def check_for_footer(attr_ids_classes):
    keywords = ['footer', 'contact']
    if any(keyword.lower() in element.lower() for element in attr_ids_classes for keyword in keywords):
        return "Footer"
    else:
        return "Not Known"

def is_listing_adresses(attr_ids_classes):
    keywords = ['listing', 'featured','properties','apartments','portfolio','multiselect__content','slideshow']
    if any(keyword.lower() in element.lower() for element in attr_ids_classes for keyword in keywords):
        return False
    else:
        return True
   
def get_headquarters(address_text):
    #pattern_hq= re.compile(r'(\bHeadquarters\b|\bHeadquarter\b|\bHQ\b|\bMain Office\b|\bCentral office\b|\bHead office\b|\bCorporate office\b|\bPrincipal office\b|\bAdministrative center\b|\bHome Office\b|\bCorporate Headquarters\b)', re.IGNORECASE)

    matches = pattern_hq.findall(address_text)
    
    if matches:
        print("\n\n\nHQ matches-->"+matches[0])
        return matches[0],'Yes'
    else:
        return "",'No'
    
    
def extract_address_from_s3(categorised_urls,domain_rows,url_type):
    addresses={}
    addresses_xpath={}
    phone_number_list = ""
    email_adrress_list = ""
    flex_number_lists = ""
    s3_url=domain_rows.loc[domain_rows['teampage_urls']==categorised_urls[url_type], 's3_html_link'].values[0]
    print('S3 URL-->'+s3_url)
    try:
        _dom = DOM.from_url(s3_url)
        _dom.clean_dom_as_default=False

        el=_dom.xpath("//frameels|//shadowels|//select|//nav|//script|//option")
        [e.getparent().remove(e) for e in el ]

        #print(_dom.text_formatted())
        search_texts=get_text_to_search(_dom.text_formatted())
        search_texts=set(search_texts)

        """ items_to_remove = ['Colorado 1365','Arizona 1839']
        search_texts = [item for item in search_texts if item not in items_to_remove] """
        print ("search_texts",search_texts)
        if search_texts:
            addresses,addresses_xpath=get_addresses_list(_dom,search_texts)
        else:
            footer_text = []
            footer_html = []
            footer_email_phone = []
            data = extract_usa_phone_numbers_and_check_is_us_phone_number(_dom.text_formatted())
            if not data:
                data = find_email_addresses(_dom.text_formatted())
            if data:
                search_texts = "in " + data[-1]
                if search_texts:
                    duplicate_addresses,duplicate_addresses_xpath=get_addresses_list(_dom,search_texts)
            
                for element,element_xpath in zip(duplicate_addresses, duplicate_addresses_xpath):
                    location=identity_footer(element_xpath)
                    attr_id_classes=get_all_ids_and_classes(_dom,element_xpath)
                    if  location == "Footer" or check_for_footer(attr_id_classes) == "Footer":
                        footer_text.append(_dom.get_text_for_xpaths(element_xpath))
                        html_code = str(_dom.content)
                        footer_check = r'class="([^"]*(footer|Footer)[^"]*)"'
                        footer_matches = re.findall(footer_check, html_code)
                        if footer_matches:
                            for footer_class in footer_matches:
                                element_pattern = rf'<[^<>]*class="{footer_class[0]}"[^<>]*>.*?</[^<>]*>'
                                element_match = re.search(element_pattern, html_code)
                                if element_match:
                                    element_html = element_match.group()
                                    footer_html.append(element_html)
                if footer_html:
                    footer_html = " ".join(str(x) for x in list(set(footer_html)))
                    pattern = r'class="([^"]*(email|phone)[^"]*)"'
                    matches = re.findall(pattern, footer_html)
                    for class_name in matches:
                        element_pattern = rf'<[^<>]*class="{class_name}"[^<>]*>.*?</[^<>]*>'
                        element_match = re.search(element_pattern, html_code)
                        if element_match:
                            element_html = element_match.group()
                            footer_email_phone.append(element_html)

            footer_social_text = " ".join(str(x) for x in list(set(footer_email_phone)))
            phone_number_string = " ".join(str(x) for x in list(set(footer_text)))
            unique_footer_social_text = phone_number_string + footer_social_text
            phone_number_list = format_phone_numbers(unique_footer_social_text)[0]
            flex_number_lists = format_phone_numbers(unique_footer_social_text)[1]
            email_adrress_list = "___".join(str(x) for x in find_email_addresses(unique_footer_social_text))
    except:
        s3_url=domain_rows.loc[domain_rows['teampage_urls']==categorised_urls[url_type], 's3_html_link'].values[0]
        c_id=domain_rows.loc[domain_rows['teampage_urls']==categorised_urls[url_type], 'client_id'].values[0]
        b_id=domain_rows.loc[domain_rows['teampage_urls']==categorised_urls[url_type], 'id'].values[0]
        domain=domain_rows.loc[domain_rows['teampage_urls']==categorised_urls[url_type], 'Domain'].values[0]
        input_url=categorised_urls[url_type]
        append_to_pd(domain_rows,input_url,'Exception Occurred try again','','',domain,0,'N/A') 
    
    return addresses,addresses_xpath,_dom,phone_number_list,flex_number_lists,email_adrress_list

def get_address_withHq_dict(hqtext,addresses):
    address_dict = {}
    hqtext = re.sub(r"[^\w\s]+", "", hqtext)
    hqtext = re.sub(r"\s+", " ", hqtext)
    
    #print("hqtext",hqtext)
    for address in addresses:
        tmp_address=address
        tmp_address = re.sub(r"[^\w\s]+", "", tmp_address)
        tmp_address = re.sub(r"\s+", " ", tmp_address)        
        index = hqtext.find(tmp_address)

        if index != -1:
            #Extract the text before the address by considering the maximum index
            preceding_text = hqtext[:index].strip()
            print("preceding_text",preceding_text)
            print("length",len(preceding_text.split()))
            #if len(preceding_text.split()) < 5:
            if not check_address_string(preceding_text,False):
                address_dict[address] = preceding_text
    return address_dict

def get_address_text_clean(content):
    for state, abbrev in us_state_to_abbrev.items():
        #pattern = r"\b" + re.escape(abbrev) + r"([\.-]?)"
        pattern = r"\b" + re.escape(abbrev) + r"\.([.-]?)"
        content = re.sub(pattern, abbrev + r"\1", content,flags=re.MULTILINE | re.IGNORECASE)
    return content

def dostart():
    
    parse = USAddressParser()
    domain_counter=1
    for domain in unique_domains:
        domain_rows = df[df['Domain'] == domain]
        
        team_page_urls = domain_rows['teampage_urls'].tolist()
        print(f"\n\n\n\n\n\n\n\n\n#### ##### ##### #### ## ##\n\n\n\nDomain Counter: {domain_counter}\n\n\n\n\n\n\n")
        print(f"Domain: {domain}\n")
        print(f"Teampage URLs: {team_page_urls}")
        domain_counter +=1
        addressCount=0
    
        categorised_urls=categorise_urls(team_page_urls,domain)
        print(categorised_urls)
        addresses={}
        addresses_xpath={}
        b_id=''
        c_id=''
        input_url=''
        page_type=''
        url_type=''
        phone_number_list = ""
        flex_number_lists = ""
        email_adrress_list = ""

        if categorised_urls['CONTACT_URL']:
            url_type='CONTACT_URL'
            page_type='CONTACT'                      
            addresses,addresses_xpath,_dom,phone_number_list,flex_number_lists,email_adrress_list=extract_address_from_s3(categorised_urls,domain_rows,url_type)

        if categorised_urls['ABOUT_URL'] and len(addresses)==0:
            url_type='ABOUT_URL'
            page_type='ABOUT'    
            addresses,addresses_xpath,_dom,phone_number_list,flex_number_lists,email_adrress_list=extract_address_from_s3(categorised_urls,domain_rows,url_type)

        if categorised_urls['OTHER_URL'] and len(addresses)==0:
            url_type='OTHER_URL'
            page_type='OTHER'    
            addresses,addresses_xpath,_dom,phone_number_list,flex_number_lists,email_adrress_list=extract_address_from_s3(categorised_urls,domain_rows,url_type)           

        if categorised_urls['HOME_URL'] and len(addresses)==0:
            url_type='HOME_URL'
            page_type='HOME'    
            addresses,addresses_xpath,_dom,phone_number_list,flex_number_lists,email_adrress_list=extract_address_from_s3(categorised_urls,domain_rows,url_type)
            
        s3_url=domain_rows.loc[domain_rows['teampage_urls']==categorised_urls[url_type], 's3_html_link'].values[0]
        c_id=domain_rows.loc[domain_rows['teampage_urls']==categorised_urls[url_type], 'client_id'].values[0]
        b_id=domain_rows.loc[domain_rows['teampage_urls']==categorised_urls[url_type], 'id'].values[0]
        input_url=categorised_urls[url_type]    
        """  print(len(addresses))
        print(addresses_xpath)
        exit()   """
        if len(addresses) > 0:
            #if len(addresses)>10: set If want to exclude listing pages
            if len(addresses)>10000:
                append_to_pd(domain_rows,input_url,'Probably listing page','','',domain,'',len(addresses),'N/A') 
            else:
                for element,element_xpath in zip(addresses, addresses_xpath):                   
                    #continue
                    #hq_elm = check_headq_parent(_dom, element_xpath)
                    hq_elm = check_headq_parent(_dom, element)
                    """  print("hq_elm_text",_dom.all_text(hq_elm))
                    exit() """
                    #Hq_Tag_snippet = _dom.tostring(hq_elm)
                    #print("Hq_Tag_snippet Tag Snippet:",Hq_Tag_snippet)
                        
                    attr_id_classes=get_all_ids_and_classes(_dom,element_xpath)
                    print(attr_id_classes)
                    not_listings=is_listing_adresses(attr_id_classes)
                    if not_listings:
                        location=identity_footer(element_xpath)
                        if location =="Not Known":
                            location=check_for_footer(attr_id_classes)   
                                               
                        #hq_text,hq=get_headquarters(_dom.all_text(element))
                        #hq_text,hq=get_headquarters(_dom.all_text(hq_elm))
                        try:
                            #address_text=get_address_text_clean(_dom.tostring(element))
                            address_text=get_address_text_clean(_dom.all_text(element))
                            print("\n\n\n\n\n\n\n\naddress_text\n\n\n\n\n\n",address_text)
                           
                            parse.feed(address_text)
                            raw_address_list=[]
                            if parse.normalized_addresses:
                                for data in  parse.normalized_addresses:
                                    raw_address_str = data['raw_address_str'] if "raw_address_str" in data  and data['raw_address_str']  else  "" 
                                    raw_address_list.append(raw_address_str)

                            address_withhq_list=get_address_withHq_dict(_dom.all_text(hq_elm),raw_address_list)
                            email_address_lists = "___".join(str(x) for x in list(set(find_email_addresses(element.getparent().inner_html)))) 
                            duplicate_phone_number_list = format_phone_numbers(_dom.all_text(element.getparent()))[0]
                            duplicate_flex_number_list = format_phone_numbers(_dom.all_text(element.getparent()))[1]

                            if not duplicate_phone_number_list and not duplicate_flex_number_list and len(parse.normalized_addresses) ==1:
                                duplicate_phone_number_list = format_phone_numbers(_dom.text_formatted())[0]
                                duplicate_flex_number_list = format_phone_numbers(_dom.text_formatted())[1]
                            if not email_address_lists and len(parse.normalized_addresses) == 1:
                                email_address_lists  = "___".join(str(x) for x in list(set(find_email_addresses(_dom.text_formatted()))))

                            if parse.normalized_addresses:
                                for data in  parse.normalized_addresses:
                                    raw_address_str = data['raw_address_str'] if "raw_address_str" in data  and data['raw_address_str']  else  "" 
                                    #print("element:",element)
                                    #print("element all text:",_dom.all_text(element))
                                    print("raw_address_str:",raw_address_str)
                                    print("address_withhq_list:",address_withhq_list)
                                    #hq_text,hq=get_headquarters(address_withhq_list[raw_address_str])
                                    try:
                                        hq_text,hq=get_headquarters(address_withhq_list[raw_address_str])
                                        
                                    except:
                                        hq_text=''
                                        hq='No'
                                        #pass
                                    append_to_pd(domain_rows,input_url,_dom.tostring(element),_dom.all_text(element),page_type,domain,_dom.tostring(hq_elm),len(addresses),location,hq_text,hq,data,duplicate_phone_number_list,duplicate_flex_number_list,email_address_lists)
                            else:
                                append_to_pd(domain_rows,input_url,_dom.tostring(element),_dom.all_text(element),page_type,domain,_dom.tostring(hq_elm),len(addresses),location,"","","",duplicate_phone_number_list,duplicate_flex_number_list,email_address_lists)
                        except:
                            append_to_pd(domain_rows,input_url,'Exception Occurred try again','','',domain,'',0,'N/A')
                         
        else:
            if phone_number_list or email_adrress_list or flex_number_lists:
                phone_number_list = phone_number_list  if phone_number_list  else ""
                email_adrress_list = email_adrress_list if email_adrress_list else ""
                flex_number_lists = flex_number_lists if flex_number_lists else ""
                append_to_pd(domain_rows,input_url,'No match found.','','',domain,'',0,f'Phone Number Footer',"","","",phone_number_list,flex_number_lists,email_adrress_list)
            else:
                append_to_pd(domain_rows,input_url,'No match found.','','',domain,'',0,'N/A')
        
        


if __name__ == '__main__':
    dostart()

    df=pd.DataFrame(html_addr_dict)
    #df.drop_duplicates(subset=['fname','lname'], inplace=True,keep="first")
    #df.to_excel(r'Biznow_Domain_output_04052023_short2.xlsx',index=False)
    df.to_excel(output_file,index=False)

    df = pd.read_excel(output_file)
    df['Address Count'] = df.groupby('Company_Website')['Company_Website'].transform('count')
    df.loc[df['Html Snippet'].str.contains('No match found.'), 'Address Count'] = 0

    # df = pd.DataFrame(add_new_address_column(df))
   
    df.to_excel(output_file,index=False)
