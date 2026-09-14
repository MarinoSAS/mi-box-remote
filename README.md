# Mi Remote

Ελληνικό web τηλεχειριστήριο για Xiaomi Mi Box / Android TV. Η σελίδα λειτουργεί σε κινητό και υπολογιστή. Η γέφυρα χρησιμοποιεί Android TV Remote v2, χωρίς ADB. Χρειάζεται ενεργό Android TV Remote Service στο Box.

## Γρήγορη εκκίνηση — Linux / macOS

Απαιτεί Python 3.11 ή νεότερη. Αποσυμπίεσε το project και άνοιξε terminal στον φάκελο `mi-box-remote`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python server.py --tv 192.168.1.50
```

Η `192.168.1.50` είναι παράδειγμα: βάλε την IP του Mi Box από Ρυθμίσεις → Δίκτυο.

Στα Windows:

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe server.py --tv 192.168.1.50
```

1. Ο υπολογιστής και το Box πρέπει να επικοινωνούν στο ίδιο τοπικό δίκτυο.
2. Άφησε το terminal ανοιχτό. Εμφανίζει το κλειδί γέφυρας.
3. Στο κινητό άνοιξε `http://IP_ΥΠΟΛΟΓΙΣΤΗ:8787` (όχι την IP του Box).
4. Στις Ρυθμίσεις βάλε το κλειδί γέφυρας.
5. Πάτα «Πρώτη φορά; Σύζευξη με TV» και γράψε τον εξαψήφιο κωδικό από την τηλεόραση.
6. Μετά από επανεκκίνηση της γέφυρας πάτα «Σύνδεση». Τα πιστοποιητικά παραμένουν στον φάκελο `data/`.

Το firewall του υπολογιστή πρέπει να επιτρέπει τη θύρα 8787 από το τοπικό δίκτυο. Το Box χρησιμοποιεί TCP 6466/6467. Το κλειδί αποθηκεύεται μόνο για τη συνεδρία της καρτέλας του browser. Το `data/` δεν σερβίρεται και εξαιρείται από git.

## GitHub Pages

Το Pages φιλοξενεί ΜΟΝΟ τον φάκελο `web/`. Η Python γέφυρα συνεχίζει να τρέχει στο σπίτι. Δεν ανεβάζουμε πιστοποιητικά, κλειδιά ή τον φάκελο `data/`.

1. Δημιούργησε νέο repository `mi-box-remote` στο GitHub και δώσε πρόσβαση στη σύνδεση GitHub του ChatGPT αν θέλεις να το δημοσιεύσει ο βοηθός.
2. Ανέβασε τα περιεχόμενα αυτού του project, μαζί με τον φάκελο `.github`, σε branch `main`.
3. Στο repository: Settings → Pages → Build and deployment → Source: **GitHub Actions**.
4. Actions → Deploy remote to GitHub Pages → Run workflow.
5. Το workflow δημοσιεύει μόνο `web/` και εμφανίζει το τελικό URL.

Εναλλακτικά, χωρίς workflow: βάλε μόνο τα περιεχόμενα του `web/` στη ρίζα ενός repository και επίλεξε Pages → Deploy from a branch → main → / (root).

### Σύνδεση από το HTTPS του GitHub

Η σελίδα GitHub Pages δεν μπορεί να βασίζεται σε απευθείας κλήσεις HTTP προς ιδιωτική IP από Safari/Chrome. Γι' αυτό η εφαρμογή προτείνει άνοιγμα της τοπικής σελίδας όταν βάζεις διεύθυνση HTTP. Το τοπικό τηλεχειριστήριο παρέχει όλες τις ίδιες λειτουργίες.

Για να παραμένεις στη σελίδα GitHub Pages χρειάζεται διεύθυνση HTTPS γέφυρας, προσβάσιμη από το κινητό, με πιστοποιητικό που εμπιστεύεται το κινητό. Υποστηρίζεται ενσωματωμένο TLS:

```bash
python server.py --tv 192.168.1.50 \
  --origin https://YOUR_USERNAME.github.io \
  --cert /absolute/path/fullchain.pem \
  --key /absolute/path/privkey.pem
```

Βάλε στη σελίδα τη διεύθυνση HTTPS που αντιστοιχεί στο πιστοποιητικό, με θύρα 8787. Το origin δεν περιλαμβάνει το όνομα repository. Οι διαδρομές πιστοποιητικών είναι παραδείγματα· η έκδοση και εγκατάστασή τους εξαρτάται από το δίκτυό σου. Δεν αρκεί ένα μη έμπιστο self-signed πιστοποιητικό. Ο browser μπορεί επιπλέον να ζητήσει άδεια τοπικού δικτύου. Δεν έχει ρυθμιστεί tunnel ή δημόσια πρόσβαση σε αυτή την έκδοση.

## Κουμπιά και όρια

- Βελάκια, ΟΚ, Πίσω, Αρχική, αναπαραγωγή/παύση.
- Ένταση / σίγαση: εξαρτώνται από fixed volume, passthrough και HDMI-CEC.
- Κανάλια: αποστέλλονται CHANNEL_UP/DOWN στην ενεργή εφαρμογή. Δεν ελέγχουν απευθείας τον τηλεοπτικό δέκτη. Κάποιες IPTV εφαρμογές δεν τα υποστηρίζουν.
- Power: αναμονή/αφύπνιση όταν το Box παραμένει διαθέσιμο στο δίκτυο. Δεν ανοίγει συσκευή αποσυνδεδεμένη από το ρεύμα.
- Netflix, YouTube, Prime Video: deep links, απαιτούν εγκατεστημένες εφαρμογές με υποστήριξη του αντίστοιχου συνδέσμου.
- Δεν περιλαμβάνει μικρόφωνο / φωνητικές εντολές.

## Έλεγχοι

```bash
python -m unittest -v test_bridge.py
node --check web/app.js
```

Οι αυτοματοποιημένοι έλεγχοι της γέφυρας χρησιμοποιούν προσομοιωμένο Mi Box. Δεν αποδεικνύουν σύζευξη ή λειτουργία συγκεκριμένων εφαρμογών σε πραγματική συσκευή. Απαιτείται τελική δοκιμή στο δικό σου Box.

Πρωτόκολλο: [androidtvremote2](https://github.com/tronikos/androidtvremote2).
GitHub Pages: [Documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages).
