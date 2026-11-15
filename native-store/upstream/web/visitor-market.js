// Country is supplied by the server, never inferred from a chosen language.
const countries=new Set(('AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ BA BB BD BE BF BG BH BI BJ BL BM BN BO BQ BR BS BT BV BW BY BZ CA CC CD CF CG CH CI CK CL CM CN CO CR CU CV CW CX CY CZ DE DJ DK DM DO DZ EC EE EG EH ER ES ET FI FJ FK FM FO FR GA GB GD GE GF GG GH GI GL GM GN GP GQ GR GS GT GU GW GY HK HM HN HR HT HU ID IE IL IM IN IO IQ IR IS IT JE JM JO JP KE KG KH KI KM KN KP KR KW KY KZ LA LB LC LI LK LR LS LT LU LV LY MA MC MD ME MF MG MH MK ML MM MN MO MP MQ MR MS MT MU MV MW MX MY MZ NA NC NE NF NG NI NL NO NP NR NU NZ OM PA PE PF PG PH PK PL PM PN PR PS PT PW PY QA RE RO RS RU RW SA SB SC SD SE SG SH SI SJ SK SL SM SN SO SR SS ST SV SX SY SZ TC TD TF TG TH TJ TK TL TM TN TO TR TT TV TW TZ UA UG UM US UY UZ VA VC VE VG VI VN VU WF WS XK YE YT ZA ZM ZW').split(' '));
const russian=new Set(['RU','BY','KZ','KG']);
const arabic=new Set(['AE','BH','DJ','DZ','EG','IQ','JO','KM','KW','LB','LY','MA','MR','OM','PS','QA','SA','SD','SO','SY','TN','YE']);
import {localeCodes,localeCountries} from './locale-registry.js?v=storefront-recovery-20261112-r1';
const supported=new Set(localeCodes);
export function visitorMarket(value){const country=countries.has(value)?value:null;return {country,international:country!==null&&country!=='TR'};}
export function countryLocale(value){const {country}=visitorMarket(value);return !country?'tr':localeCountries[country]||(russian.has(country)?'ru':arabic.has(country)?'ar':'en');}
export function initialLocale({requested,stored,country}={}){return supported.has(requested)?requested:supported.has(stored)?stored:countryLocale(country);}
