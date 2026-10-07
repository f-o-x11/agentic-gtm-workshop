"""Exact account and person identity checks without legacy runtime imports."""
from datetime import datetime, timezone
import json
import re
from urllib.parse import urlparse
from engine.database import digest


def timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return result if result.tzinfo else None
    except ValueError:
        return None


def fresh(value, seconds, at=None):
    date = timestamp(value)
    return date is not None and 0 <= ((at or datetime.now(timezone.utc)) - date).total_seconds() <= seconds


def domain(value):
    if not isinstance(value, str) or any(c.isspace() for c in value):
        return ''
    parsed = urlparse(value if '://' in value else 'https://' + value)
    name = (parsed.hostname or '').lower().removeprefix('www.').rstrip('.')
    if parsed.username or parsed.password or not re.fullmatch(r'[a-z0-9][a-z0-9.-]*\.[a-z]{2,}', name):
        return ''
    return name


def email(value):
    value = str(value or '').strip().lower()
    return value if re.fullmatch(r'[a-z0-9._+%-]+@[a-z0-9.-]+\.[a-z]{2,}', value) else ''


def profile(value):
    if not isinstance(value, str):
        return ''
    parsed = urlparse(value)
    match = re.fullmatch(r'/in/([^/]+)/?', parsed.path)
    if (parsed.scheme not in ('http', 'https') or parsed.hostname not in ('www.linkedin.com', 'linkedin.com')
            or parsed.username or parsed.password or not match):
        return ''
    return 'https://www.linkedin.com/in/' + match[1].lower()


def normalized(value):
    return re.sub(r'[^a-z0-9]', '', str(value or '').lower())


# Recognized names from pinned pycountry ISO3166-1 data; no runtime dependency.
# https://raw.githubusercontent.com/pycountry/pycountry/4c6a69927a25326a69bf753671fb571bb437cd7d/src/pycountry/databases/iso3166-1.json
COUNTRY_NAMES = frozenset("Afghanistan|Albania|Algeria|American Samoa|Andorra|Angola|Anguilla|Antarctica|Antigua and Barbuda|Argentina|Armenia|Aruba|Australia|Austria|Azerbaijan|Bahamas|Bahrain|Bangladesh|Barbados|Belarus|Belgium|Belize|Benin|Bermuda|Bhutan|Bolivia|Bolivia, Plurinational State of|Bonaire, Sint Eustatius and Saba|Bosnia and Herzegovina|Botswana|Bouvet Island|Brazil|British Indian Ocean Territory|Brunei Darussalam|Bulgaria|Burkina Faso|Burundi|Cabo Verde|Cambodia|Cameroon|Canada|Cayman Islands|Central African Republic|Chad|Chile|China|Christmas Island|Cocos (Keeling) Islands|Colombia|Comoros|Congo|Congo, The Democratic Republic of the|Cook Islands|Costa Rica|Croatia|Cuba|Curaçao|Cyprus|Czechia|Côte d'Ivoire|Denmark|Djibouti|Dominica|Dominican Republic|Ecuador|Egypt|El Salvador|Equatorial Guinea|Eritrea|Estonia|Eswatini|Ethiopia|Falkland Islands (Malvinas)|Faroe Islands|Fiji|Finland|France|French Guiana|French Polynesia|French Southern Territories|Gabon|Gambia|Georgia|Germany|Ghana|Gibraltar|Greece|Greenland|Grenada|Guadeloupe|Guam|Guatemala|Guernsey|Guinea|Guinea-Bissau|Guyana|Haiti|Heard Island and McDonald Islands|Holy See (Vatican City State)|Honduras|Hong Kong|Hungary|Iceland|India|Indonesia|Iran|Iran, Islamic Republic of|Iraq|Ireland|Isle of Man|Israel|Italy|Jamaica|Japan|Jersey|Jordan|Kazakhstan|Kenya|Kiribati|Korea, Democratic People's Republic of|Korea, Republic of|Kuwait|Kyrgyzstan|Lao People's Democratic Republic|Laos|Latvia|Lebanon|Lesotho|Liberia|Libya|Liechtenstein|Lithuania|Luxembourg|Macao|Madagascar|Malawi|Malaysia|Maldives|Mali|Malta|Marshall Islands|Martinique|Mauritania|Mauritius|Mayotte|Mexico|Micronesia, Federated States of|Moldova|Moldova, Republic of|Monaco|Mongolia|Montenegro|Montserrat|Morocco|Mozambique|Myanmar|Namibia|Nauru|Nepal|Netherlands|New Caledonia|New Zealand|Nicaragua|Niger|Nigeria|Niue|Norfolk Island|North Korea|North Macedonia|Northern Mariana Islands|Norway|Oman|Pakistan|Palau|Palestine, State of|Panama|Papua New Guinea|Paraguay|Peru|Philippines|Pitcairn|Poland|Portugal|Puerto Rico|Qatar|Romania|Russian Federation|Rwanda|Réunion|Saint Barthélemy|Saint Helena, Ascension and Tristan da Cunha|Saint Kitts and Nevis|Saint Lucia|Saint Martin (French part)|Saint Pierre and Miquelon|Saint Vincent and the Grenadines|Samoa|San Marino|Sao Tome and Principe|Saudi Arabia|Senegal|Serbia|Seychelles|Sierra Leone|Singapore|Sint Maarten (Dutch part)|Slovakia|Slovenia|Solomon Islands|Somalia|South Africa|South Georgia and the South Sandwich Islands|South Korea|South Sudan|Spain|Sri Lanka|Sudan|Suriname|Svalbard and Jan Mayen|Sweden|Switzerland|Syria|Syrian Arab Republic|Taiwan|Taiwan, Province of China|Tajikistan|Tanzania|Tanzania, United Republic of|Thailand|Timor-Leste|Togo|Tokelau|Tonga|Trinidad and Tobago|Tunisia|Turkmenistan|Turks and Caicos Islands|Tuvalu|Türkiye|Uganda|Ukraine|United Arab Emirates|United Kingdom|United States|United States Minor Outlying Islands|Uruguay|Uzbekistan|Vanuatu|Venezuela|Venezuela, Bolivarian Republic of|Viet Nam|Vietnam|Virgin Islands, British|Virgin Islands, U.S.|Wallis and Futuna|Western Sahara|Yemen|Zambia|Zimbabwe|Åland Islands".split("|"))


def country(value):
    """Map documented common aliases, without guessing an unknown country."""
    text = ' '.join(str(value or '').strip().split())
    key = re.sub(r'[.\s_-]', '', text).casefold()
    aliases = {
        'United States': ('us', 'usa', 'unitedstates', 'unitedstatesofamerica'),
        'United Kingdom': ('uk', 'gb', 'gbr', 'unitedkingdom', 'greatbritain'),
        'Canada': ('ca', 'can', 'canada'), 'Australia': ('au', 'aus', 'australia'),
        'Germany': ('de', 'deu', 'germany'), 'France': ('fr', 'fra', 'france'),
        'Ireland': ('ie', 'irl', 'ireland'), 'Israel': ('il', 'isr', 'israel'),
        'Netherlands': ('nl', 'nld', 'netherlands'), 'Singapore': ('sg', 'sgp', 'singapore'),
        'United Arab Emirates': ('ae', 'are', 'uae', 'unitedarabemirates'),
    }
    return next((name for name, values in aliases.items() if key in values),
        next((name for name in COUNTRY_NAMES if name.casefold() == text.casefold()), text))


def account_domains(store, employer):
    aliases = store.setting('native.corporate-email-domains.json', [])
    if not isinstance(aliases, list):
        aliases = []
    return [employer] + sorted({domain(row.get('email_domain')) for row in aliases
        if isinstance(row, dict) and domain(row.get('account_domain')) == employer
        and row.get('verification') == 'official_publication' and row.get('evidence_url')
        and row.get('evidence_sha256') and domain(row.get('email_domain'))})


def load(value):
    if isinstance(value, dict):
        return value
    try:
        obj = json.loads(value or '{}')
        return obj if isinstance(obj, dict) else {}
    except (TypeError, ValueError):
        return {}


def account_layers(account):
    data = load(account.get('data_json'))
    rows = [data] + [load(data.get(key)) for key in ('postgres', 'native', 'workbook')]
    aliases = load(data.get('source_aliases'))
    for values in aliases.values():
        if isinstance(values, list):
            rows.extend(value for value in values if isinstance(value, dict))
    return rows


def account_issues(account, policy):
    if not account:
        return ['Current account is absent.']
    issues = []
    layers = account_layers(account)
    for row in layers:
        if (row.get('clean_excluded')
                or row.get('Priority') == 'Exclude' or row.get('clean_relationship') or row.get('Relationship')
                or row.get('state') in ('excluded', 'suppressed') or row.get('domain_valid') is False):
            issues.append('Current account is excluded or has an existing relationship.')
    actual_country = country(next((r.get('country') or r.get('Country') for r in layers if r.get('country') or r.get('Country')), None))
    allowed = [country(value) for value in policy.get('recipient_company_countries', [])]
    if (actual_country.casefold() not in {name.casefold() for name in COUNTRY_NAMES}
            or actual_country.casefold() not in {value.casefold() for value in allowed if value}):
        issues.append('Current company country is unknown or outside authorized scope: ' + (actual_country or 'unknown') + '.')
    return issues


def find_person(store, recipient, employer, wanted_profile=''):
    rows = store.rows('SELECT * FROM people WHERE email=? AND domain=?', (recipient, employer))
    if wanted_profile:
        rows = [r for r in rows if profile(r.get('profile')) == wanted_profile]
    identities = {profile(r.get('profile')) for r in rows if profile(r.get('profile'))}
    if not rows or len(identities) > 1:
        return None, ['Current person/profile identity is missing or ambiguous.']
    # A new verified identity supersedes stale preparation and employment flags.
    rows.sort(key=lambda row: (load(load(row.get('data_json')).get('identity') or
                    load(row.get('data_json')).get('current_employment')).get('status') == 'confirmed_current',
                    row.get('observed_at') or '', str(row.get('source', '')).startswith('native')), reverse=True)
    person = rows[0]
    for row in rows:
        data = load(row.get('data_json'))
        current = (row.get('observed_at') or '') >= (person.get('observed_at') or '')
        if (data.get('status') == 'suppressed' or data.get('relationship') or data.get('Relationship')
                or (current and (data.get('domain_mismatch') is True or data.get('email_ok') is False
                                 or data.get('status') in ('retired', 'employment_disputed', 'inactive')))):
            return person, ['Current person has an identity, status or relationship hold.']
    return person, []


def person_issues(store, person, employer, at=None, require_profile=False):
    if not person:
        return ['Current person is absent.']
    raw = load(person.get('data_json'))
    recipient = email(person.get('email'))
    url = profile(person.get('profile'))
    issues = []
    if not recipient or recipient.rsplit('@', 1)[-1] not in account_domains(store, employer) or domain(person.get('domain')) != employer:
        issues.append('Work email and current account domain differ.')
    if require_profile and not url:
        issues.append('Current LinkedIn person profile is missing.')
    title = person.get('title') or raw.get('title') or raw.get('Role') or ''
    proof = load(raw.get('identity') or raw.get('current_employment'))
    if not proof:
        row = store.one('SELECT data_json,digest FROM source_records WHERE source=? AND record_key=?', ('identity.current', recipient))
        if row and digest(load(row['data_json'])) != row['digest']:
            issues.append('Current employment source receipt changed.')
        proof = load(row.get('data_json')) if row else {}
    if proof.get('status') != 'confirmed_current':
        issues.append('Current employer evidence is not confirmed.')
    proof_domain = domain(proof.get('domain') or load(proof.get('native_name_fields')).get('domain'))
    proof_profile = profile(proof.get('clean_linkedin') or proof.get('profile_url') or proof.get('linkedin'))
    proof_title = proof.get('clean_title') or proof.get('title')
    if (proof_domain != employer or (require_profile and proof_profile != url)
            or (proof_title and normalized(proof_title) != normalized(title))):
        issues.append('Current employer, profile or title evidence differs from the actual person.')
    proof_name = proof.get('profile_name') or proof.get('clean_name')
    if proof_name and normalized(proof_name) != normalized(person.get('name')):
        issues.append('Current person name differs from the native profile.')
    observed = proof.get('profile_fetched_at') or proof.get('observed_at') or proof.get('checked_at')
    if not fresh(observed, 7 * 86400, at):
        issues.append('Current employment evidence is stale or has no actual timestamp.')
    if not proof.get('provider') and not proof.get('source') and not proof.get('native_name_fields'):
        issues.append('Current employment source provenance is missing.')
    if require_profile:
        return issues  # An invitation does not require email deliverability validation.
    verdict = raw.get('zb_status') or raw.get('Email status')
    checked = raw.get('zb_checked_at') or raw.get('checked_at') or raw.get('Email checked')
    valid_email = verdict == 'valid' and fresh(checked, 7 * 86400, at)
    if not valid_email:
        for row in store.rows("SELECT data_json,digest FROM source_records WHERE source='postgres.contacts' AND json_extract(data_json,'$.email')=?", (recipient,)):
            evidence = load(row['data_json'])
            if (digest(evidence) == row['digest'] and domain(evidence.get('domain')) == employer
                    and profile(evidence.get('linkedin_url')) == url and evidence.get('zb_status') == 'valid'
                    and evidence.get('email_ok') is not False and evidence.get('domain_mismatch') is not True
                    and fresh(evidence.get('zb_checked_at'), 7 * 86400, at)):
                valid_email = True
                break
    if not valid_email:
        verification = load(raw.get('email_verification'))
        valid_email = (email(verification.get('email')) == recipient
                       and verification.get('status') == 'valid' and bool(verification.get('provider'))
                       and fresh(verification.get('checked_at'), 7 * 86400, at))
    if not valid_email:
        issues.append('Current work email lacks fresh valid deliverability evidence.')
    return issues


from email.message import EmailMessage
from email.policy import SMTP
from html import escape, unescape
from html.parser import HTMLParser
import re

PHRASES = ('caught my attention', 'explore a bigger opportunity', 'unlock', 'delve',
           'leverage', 'not just', 'game changer', 'game-changing', 'revolutionize',
           'i hope this email finds you well', 'synergy', 'transformative')
URL = re.compile(r'https?://|www\.|(?<![@\w])(?:[a-z0-9-]+\.)+(?:com|io|ai|co|net|org|edu|gov|tech|app|dev|us|ca)(?:[/?#]|\b)', re.I)


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.words, self.unsafe = [], False
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'iframe', 'object', 'form'):
            self.unsafe = True
        if any(k.startswith('on') or str(v).lower().startswith('javascript:') for k, v in attrs):
            self.unsafe = True
    def handle_data(self, text):
        self.words.append(text)


def plain_from_html(value):
    parser = Text()
    parser.feed(value or '')
    return ' '.join(parser.words), parser.unsafe


def copy_fields(payload):
    values = []
    def visit(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in ('subject', 'body', 'body_html', 'html', 'plain', 'text', 'message', 'content') and isinstance(item, str):
                    values.append((key, item))
                elif isinstance(item, (dict, list)):
                    visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)
    visit(payload)
    return values


def validate(payload, initial_email=False):
    issues = []
    fields = copy_fields(payload)
    for key, text in fields:
        rendered, unsafe = plain_from_html(text) if key in ('body_html', 'html') else (text, False)
        rendered = unescape(rendered)
        if any(char in rendered for char in ('\u2014', '\u2013')) or ' -- ' in rendered:
            issues.append('Copy contains prohibited dash punctuation.')
        if any(re.search(r'\b' + re.escape(phrase) + r'\b', rendered, re.I) for phrase in PHRASES):
            issues.append('Copy contains generic AI phrasing.')
        if unsafe:
            issues.append('HTML contains active or unsafe content.')
        if key == 'subject' and ('\r' in text or '\n' in text or not text.strip()):
            issues.append('Email subject is empty or contains header injection.')
        if initial_email and (URL.search(rendered) or re.search(r'<\s*a\b|href\s*=|<\s*img\b', text, re.I)):
            issues.append('Initial email contains a link.')
    if initial_email:
        body = payload.get('body') or payload.get('plain') or payload.get('text')
        if not isinstance(body, str) or not body.strip():
            issues.append('Initial email has no plain text body.')
    html = payload.get('body_html') or payload.get('html')
    plain = payload.get('body') or payload.get('plain') or payload.get('text')
    if html and plain:
        rendered, _ = plain_from_html(html)
        if re.sub(r'\s+', '', unescape(rendered)) != re.sub(r'\s+', '', plain):
            issues.append('HTML and plain text email copy differ.')
    return sorted(set(issues))


def format_email(sender, recipient, subject, plain, html=None):
    payload = {'subject': subject, 'body': plain, 'body_html': html}
    issues = validate(payload)
    if issues:
        raise ValueError(' '.join(issues))
    if any('\n' in value or '\r' in value for value in (sender, recipient)):
        raise ValueError('Email header contains a newline.')
    message = EmailMessage(policy=SMTP)
    message['From'], message['To'], message['Subject'] = sender, recipient, subject
    message.set_content(plain.rstrip() + '\n')
    message.add_alternative(html or '<p>' + escape(plain).replace('\n\n', '</p><p>').replace('\n', '<br>') + '</p>', subtype='html')
    return message.as_bytes()
