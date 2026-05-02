import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import struct, csv, io, os, sys, re

# ── ROM constants ────────────────────────────────────────────────
BLOCK_AREA_END = {32: 2030418}
OVERALL_BASE   = {30: 1952292, 32: 2003636}
n_teams = 30

# ── Binary helpers ───────────────────────────────────────────────
def u32(d, o): return struct.unpack_from('>I', d, o)[0]
def u16(d, o): return struct.unpack_from('>H', d, o)[0]

def read_str(d, o, length):
    s = ''
    for i in range(length):
        b = d[o + i]
        if b == 0: break
        s += chr(b)
    return s.strip()

def tm_ptrs(d):
    return [u32(d, 782 + i * 4) for i in range(n_teams)]

def read_team_name(d, ptr):
    pos = ptr + u16(d, ptr + 4)
    city_len  = u16(d, pos); city  = read_str(d, pos+2, city_len-2);  pos += city_len
    abv_len   = u16(d, pos); abv   = read_str(d, pos+2, abv_len-2);   pos += abv_len
    nm_len    = u16(d, pos); name  = read_str(d, pos+2, nm_len-2);    pos += nm_len
    arena_len = u16(d, pos); arena = read_str(d, pos+2, arena_len-2)
    return {'city': city, 'abv': abv, 'name': name, 'arena': arena}

def parse_name_sections(d, start):
    pos = start
    for _ in range(4):
        if pos + 2 > len(d): break
        sec = u16(d, pos)
        if sec < 2: break
        pos += sec
    return pos - start

def build_name_section(s):
    b = s.encode('ascii')
    if len(b) % 2: b += b'\x00'
    sec = 2 + len(b)
    return bytes([sec >> 8, sec & 0xFF]) + b

def read_goalie_count(d, ptr):
    h4 = f'{d[ptr+80]:02x}{d[ptr+81]:02x}'
    idx = h4.find('0')
    return 4 if idx < 0 else idx

def goalie_bytes(ng):
    return {1:[0x10,0x00], 2:[0x11,0x00], 3:[0x11,0x10]}.get(ng, [0x11,0x11])

def build_default_lines(ng, nf):
    ff, fd = ng+1, ng+nf+1
    line = [1, fd, fd+1, ff, ff+1, ff+2, ff+3]
    buf, pos = bytearray(64), 0
    for _ in range(8):
        for p in line: buf[pos] = p; pos += 1
        buf[pos] = 0; pos += 1
    return bytes(buf)

def recalc_checksum(data):
    ck = 0
    i = 0x200
    while i + 1 < len(data):
        ck = (ck + (data[i] << 8) + data[i+1]) & 0xFFFF
        i += 2
    data[0x18E] = (ck >> 8) & 0xFF
    data[0x18F] =  ck       & 0xFF

# ── Player export ────────────────────────────────────────────────
def export_players(raw):
    d, rows = bytes(raw), []
    for ptr in tm_ptrs(d):
        abv  = read_team_name(d, ptr)['abv']
        ng   = read_goalie_count(d, ptr)
        nf   = (d[ptr+79] >> 4) & 0xF
        pos  = ptr + u16(d, ptr)
        pidx = 0
        while pos + 1 < len(d):
            pnl = u16(d, pos)
            if pnl < 4: break
            pos += 2; pidx += 1
            nm = ''
            for _ in range(pnl - 2):
                ch = d[pos]; pos += 1
                if ch: nm += chr(ch)
            jno = f'{d[pos]:02x}'; pos += 1
            att = []
            for _ in range(7):
                att.append((d[pos]>>4)&0xF); att.append(d[pos]&0xF); pos += 1
            pt = 'G' if pidx<=ng else ('F' if pidx<=ng+nf else 'D')
            if pt == 'G':
                tot = int(att[1]*4.5)+int(att[4]*4.5)+int(att[5]*4.5)+att[10]+att[11]+att[12]+att[13]
            else:
                tot = att[1]*2+att[2]*3+att[3]*3+att[4]*2+att[5]+att[6]*2+att[8]*3+att[9]*2+att[10]+att[12]
            ovr = min(99, 25+tot//2 if tot<50 else tot)
            p1 = nm.split(' ', 1)
            rows.append({
                'First':p1[0],'Last':p1[1] if len(p1)>1 else '','Abv':abv,
                'Pos':pt,'JNo':jno,'Ovr':ovr,
                'Wgt':att[0],'Agl':att[1],'Spd':att[2],'OfA':att[3],'DfA':att[4],
                'ShP-PkC':att[5],'Chk':att[6],'Hnd':att[7],'StH':att[8],'ShA':att[9],
                'End-StR':att[10],'Rgh-StL':att[11],'Pas-GlR':att[12],'Agr-GlL':att[13]
            })
    return rows

# ── Player import ────────────────────────────────────────────────
P_FIELDS = ['First','Last','Abv','Pos','JNo','Ovr','Wgt','Agl','Spd','OfA','DfA',
            'ShP-PkC','Chk','Hnd','StH','ShA','End-StR','Rgh-StL','Pas-GlR','Agr-GlL']
NF_FIELDS = ['Agl','Spd','OfA','DfA','ShP-PkC','Chk','StH','ShA','End-StR','Rgh-StL','Pas-GlR','Agr-GlL']
NAME_RE   = re.compile(r"^[A-Za-z.'\-]*$")

def build_attr_nibbles(p):
    h = lambda v: format(int(v), 'x')
    return (h(p['Wgt'])+str(p['Agl'])+str(p['Spd'])+str(p['OfA'])+str(p['DfA'])
           +str(p['ShP-PkC'])+str(p['Chk'])+h(p['Hnd'])
           +str(p['StH'])+str(p['ShA'])+str(p['End-StR'])
           +str(p['Rgh-StL'])+str(p['Pas-GlR'])+str(p['Agr-GlL']))

def import_players(rom_bytes, player_rows):
    if not player_rows: raise ValueError('CSV is empty.')
    missing = [f for f in P_FIELDS if f not in player_rows[0]]
    if missing: raise ValueError(f"CSV missing columns: {', '.join(missing)}")

    for ri, p in enumerate(player_rows):
        lbl = f'Row {ri+1}'
        if p['Pos'] not in ('G','F','D'):
            raise ValueError(f"{lbl}: Pos must be G, F, or D")
        first, last = str(p.get('First','')), str(p.get('Last',''))
        if len(first)+1+len(last) > 18:
            raise ValueError(f"{lbl}: \"{first} {last}\" is {len(first)+1+len(last)} chars — max 18")
        if not NAME_RE.match(first): raise ValueError(f"{lbl}: First \"{first}\" has invalid characters")
        if not NAME_RE.match(last):  raise ValueError(f"{lbl}: Last \"{last}\" has invalid characters")
        if not re.match(r'^[0-9a-fA-F]{1,2}$', str(p['JNo'])):
            raise ValueError(f"{lbl}: JNo must be hex 00–FF")
        for f in ('Wgt','Hnd'):
            if not (0 <= int(p[f]) <= 15): raise ValueError(f"{lbl}: {f} must be 0–15")
        for f in NF_FIELDS:
            if not (0 <= int(p[f]) <= 6):  raise ValueError(f"{lbl}: {f} must be 0–6")

    abv_order, team_map = [], {}
    for row in player_rows:
        abv = row['Abv'].strip()
        if abv not in team_map: team_map[abv]=[]; abv_order.append(abv)
        team_map[abv].append(row)
    if len(abv_order) != n_teams:
        raise ValueError(f"CSV has {len(abv_order)} teams — expected {n_teams}.")

    team_info = []
    for abv in abv_order:
        players = team_map[abv]
        tb = ng = nf = nd = phase = 0
        for p in players:
            nl = len(str(p['First']))+len(str(p['Last']))
            tb += nl+11 if (nl+1)%2==0 else nl+12
            if p['Pos']=='G':
                if phase>0: raise ValueError(f"{abv}: goalies must come before forwards and defense")
                ng+=1
            elif p['Pos']=='F':
                if phase>1: raise ValueError(f"{abv}: forwards must come before defense")
                phase=1; nf+=1
            else:
                phase=2; nd+=1
        if not (1<=ng<=4):  raise ValueError(f"{abv}: goalies must be 1–4 (found {ng})")
        if not (1<=nf<=15): raise ValueError(f"{abv}: forwards must be 1–15 (found {nf})")
        if not (1<=nd<=15): raise ValueError(f"{abv}: defense must be 1–15 (found {nd})")
        team_info.append({'abv':abv,'players':players,'tb':tb,'ng':ng,'nf':nf,'nd':nd})

    data  = bytearray(rom_bytes)
    db    = bytes(data)
    ptrs  = tm_ptrs(db)
    tm_offs = [u16(db, p+4) for p in ptrs]
    total_space = sum(t-146 for t in tm_offs)

    base  = total_space // n_teams
    beven = base if base%2==0 else base-1
    extra = total_space - beven*n_teams
    spaces = [beven+2 if i>=n_teams-(extra//2) else beven for i in range(n_teams)]

    for i,t in enumerate(team_info):
        needed = t['tb']+2
        if needed>spaces[i]:
            raise ValueError(f"{t['abv']}: needs {needed} bytes, only {spaces[i]} available")

    area_end = BLOCK_AREA_END.get(n_teams)
    name_data = []
    for i,ptr in enumerate(ptrs):
        ns = ptr + tm_offs[i]
        if i < n_teams-1:       name_data.append(bytes(data[ns:ptrs[i+1]]))
        elif area_end is not None: name_data.append(bytes(data[ns:area_end]))
        else:
            sz = parse_name_sections(db, ns)
            name_data.append(bytes(data[ns:ns+sz]))

    old_hdrs     = [bytes(data[p:p+146]) for p in ptrs]
    old_blk_end  = area_end or (ptrs[-1]+tm_offs[-1]+len(name_data[-1]))
    blocks, new_ptrs = [], [ptrs[0]]

    for i,t in enumerate(team_info):
        sp     = spaces[i]
        empty  = sp - t['tb'] - 2
        pl_off = 146 + empty
        tm_off = 146 + sp
        bsz    = tm_off + len(name_data[i])
        blk    = bytearray(bsz)
        blk[:146] = old_hdrs[i]
        struct.pack_into('>H', blk, 0, pl_off)
        struct.pack_into('>H', blk, 4, tm_off)
        blk[79]   = ((t['nf']&0xF)<<4)|(t['nd']&0xF)
        gb        = goalie_bytes(t['ng'])
        blk[80], blk[81] = gb[0], gb[1]
        blk[82:146] = build_default_lines(t['ng'], t['nf'])
        for j in range(146, pl_off): blk[j] = 0xFF
        wp = pl_off
        for p in t['players']:
            nws  = str(p['First'])+' '+str(p['Last'])
            nb   = nws.encode('ascii')
            nml  = len(nws)+2 if len(nws)%2==0 else len(nws)+3
            blk[wp]=0x00; blk[wp+1]=nml; wp+=2
            blk[wp:wp+len(nb)]=nb; wp+=len(nb)
            if len(nws)%2: blk[wp]=0x00; wp+=1
            blk[wp]=int(str(p['JNo']),16); wp+=1
            attr = build_attr_nibbles(p)
            for b in range(7): blk[wp]=int(attr[b*2:b*2+2],16); wp+=1
        blk[wp]=0x00; blk[wp+1]=0x02
        blk[tm_off:tm_off+len(name_data[i])]=name_data[i]
        blocks.append(bytes(blk))
        if i<n_teams-1: new_ptrs.append(new_ptrs[i]+bsz)

    pre  = bytes(data[:ptrs[0]])
    post = bytes(data[old_blk_end:])
    rom  = bytearray(len(pre)+sum(len(b) for b in blocks)+len(post))
    wp   = 0
    rom[wp:wp+len(pre)]=pre; wp+=len(pre)
    for b in blocks: rom[wp:wp+len(b)]=b; wp+=len(b)
    rom[wp:]=post
    for i in range(n_teams): struct.pack_into('>I', rom, 782+i*4, new_ptrs[i])
    recalc_checksum(rom)
    return bytes(rom)

# ── Team export ──────────────────────────────────────────────────
def export_teams(raw):
    d, rows = bytes(raw), []
    for i,ptr in enumerate(tm_ptrs(d)):
        t   = read_team_name(d, ptr)
        b76,b77,b78 = d[ptr+76],d[ptr+77],d[ptr+78]
        rows.append({
            'Team City':t['city'],'Abv':t['abv'],'Team Name':t['name'],'Arena':t['arena'],
            'Overall':d[OVERALL_BASE[n_teams]+i],
            'Offense':(b76>>4)&0xF,'Defense':b76&0xF,
            'PK':(b77>>4)&0xF,'PP':b77&0xF,
            'Home':(b78>>4)&0xF,'Road':b78&0xF,
        })
    return rows

# ── Team import ──────────────────────────────────────────────────
def import_teams(rom_bytes, rows):
    if len(rows)!=n_teams:
        raise ValueError(f"CSV has {len(rows)} rows — expected {n_teams}.")
    for i,row in enumerate(rows):
        lbl=f'Row {i+1}'
        if not (0<=int(row['Overall'])<=99): raise ValueError(f"{lbl}: Overall must be 0–99")
        if not (0<=int(row['Offense'])<=7) or not (0<=int(row['Defense'])<=7):
            raise ValueError(f"{lbl}: Offense/Defense must be 0–7")
        if not (0<=int(row['PK'])<=2) or not (0<=int(row['PP'])<=2):
            raise ValueError(f"{lbl}: PK/PP must be 0–2")
        if not (0<=int(row['Home'])<=2): raise ValueError(f"{lbl}: Home must be 0–2")
        if not (0<=int(row['Road'])<=3): raise ValueError(f"{lbl}: Road must be 0–3")

    has_names = 'Arena' in rows[0]
    if has_names:
        seen=set()
        for i,row in enumerate(rows):
            lbl=f'Row {i+1}'
            for f in ('Team City','Team Name','Arena'):
                if not row.get(f,'').strip(): raise ValueError(f"{lbl}: {f} must not be empty")
            abv=row.get('Abv','').strip()
            if not re.match(r'^[A-Za-z0-9]{2,3}$', abv):
                raise ValueError(f"{lbl}: Abv must be 2–3 letters/numbers")
            if abv.upper() in seen: raise ValueError(f"{lbl}: Abv \"{abv}\" is a duplicate")
            seen.add(abv.upper())

    data = bytearray(rom_bytes)
    db   = bytes(data)
    ptrs = tm_ptrs(db)
    tm_offs  = [u16(db, p+4) for p in ptrs]
    old_pl_offs = [u16(db, p) for p in ptrs]

    if not has_names:
        for i,row in enumerate(rows):
            data[OVERALL_BASE[n_teams]+i]=int(row['Overall'])
            ptr=ptrs[i]
            data[ptr+76]=(int(row['Offense'])<<4)|int(row['Defense'])
            data[ptr+77]=(int(row['PK'])<<4)|int(row['PP'])
            data[ptr+78]=(int(row['Home'])<<4)|int(row['Road'])
        recalc_checksum(data)
        return bytes(data)

    area_end = BLOCK_AREA_END.get(n_teams)
    if area_end is None:
        ns = ptrs[-1]+tm_offs[-1]
        area_end = ns + parse_name_sections(db, ns)
    block_sizes = [ptrs[i+1]-ptrs[i] if i<n_teams-1 else area_end-ptrs[i] for i in range(n_teams)]

    new_names = []
    for row in rows:
        new_names.append(b''.join([
            build_name_section(row['Team City'].strip()),
            build_name_section(row['Abv'].strip()),
            build_name_section(row['Team Name'].strip()),
            build_name_section(row['Arena'].strip()),
        ]))

    for i,row in enumerate(rows):
        pb  = tm_offs[i] - old_pl_offs[i]
        nfr = block_sizes[i] - 146 - pb - len(new_names[i])
        if nfr < 0:
            raise ValueError(f"Row {i+1} ({row.get('Abv','').strip()}): names are {-nfr} bytes too large")

    for i,row in enumerate(rows):
        ptr    = ptrs[i]
        opl    = old_pl_offs[i]
        otm    = tm_offs[i]
        pb     = otm - opl
        nns    = len(new_names[i])
        tb     = block_sizes[i]
        nfr    = tb - 146 - pb - nns
        npl    = 146 + nfr
        ntm    = tb - nns
        ps     = bytes(data[ptr+opl:ptr+otm])
        struct.pack_into('>H', data, ptr+0, npl)
        struct.pack_into('>H', data, ptr+4, ntm)
        data[ptr+76]=(int(row['Offense'])<<4)|int(row['Defense'])
        data[ptr+77]=(int(row['PK'])<<4)|int(row['PP'])
        data[ptr+78]=(int(row['Home'])<<4)|int(row['Road'])
        for j in range(146, npl): data[ptr+j]=0xFF
        data[ptr+npl:ptr+npl+pb]=ps
        data[ptr+ntm:ptr+ntm+nns]=new_names[i]

    for i,row in enumerate(rows):
        data[OVERALL_BASE[n_teams]+i]=int(row['Overall'])
    recalc_checksum(data)
    return bytes(data)

# ── CSV helpers ──────────────────────────────────────────────────
def rows_to_csv(rows):
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=list(rows[0].keys()), lineterminator='\r\n')
    w.writeheader(); w.writerows(rows)
    return out.getvalue()

def csv_to_rows(text):
    r = csv.DictReader(io.StringIO(text))
    return [row for row in r if any(v.strip() for v in row.values())]

# ── Button style (set up once on first App init) ─────────────────
def _setup_button_style():
    s = ttk.Style()
    s.configure('Roster.TButton', font=('Arial', 10), padding=(24, 6))

# ── UI ────────────────────────────────────────────────────────────
def bundled(name):
    """Files packed inside the exe via --add-data (e.g. icon.ico)."""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)

def beside_exe(name):
    """Files placed next to the exe by the user (e.g. cover.png)."""
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), name)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), name)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        _setup_button_style()
        self.title("NHL '94 Roster Tool — GENS")
        self.resizable(False, False)
        self.configure(bg='white')
        if sys.platform == 'darwin':
            win_ico = bundled('window.icns')
        else:
            win_ico = bundled('window.ico')
        if os.path.exists(win_ico):
            self.iconbitmap(win_ico)

        # Cover image — prefer user-supplied file beside exe, fall back to bundled default
        cover = beside_exe('cover.png')
        if not os.path.exists(cover):
            cover = bundled('cover.png')
        if os.path.exists(cover):
            try:
                from PIL import Image, ImageTk
                img = Image.open(cover)
                img.thumbnail((640, 320), Image.LANCZOS)
                self._img = ImageTk.PhotoImage(img)
                tk.Label(self, image=self._img, bg='white').pack(pady=(20,10))
            except Exception:
                self._header()
        else:
            self._header()

        # 30 / 32 toggle
        tf = tk.Frame(self, bg='white')
        tf.pack(pady=(4,16))
        self._btn30 = self._toggle_btn(tf, '30 Teams', 30)
        self._btn32 = self._toggle_btn(tf, '32 Teams', 32)
        self._nteams = 30
        self._refresh_toggle()

        # Player / Team button groups
        outer = tk.Frame(self, bg='white')
        outer.pack(padx=40, pady=(0, 24))

        groups = [
            ('Player Data', False, [
                ('Export', self.do_export_players),
                ('Import', self.do_import_players),
            ]),
            ('Team Data', True, [
                ('Export', self.do_export_teams),
                ('Import', self.do_import_teams),
            ]),
        ]
        for col, (label, underline, btns) in enumerate(groups):
            grp = tk.Frame(outer, bg='white')
            grp.grid(row=0, column=col, padx=20, sticky='n')
            font = ('Arial', 9, 'bold underline') if underline else ('Arial', 9, 'bold')
            tk.Label(grp, text=label, font=font,
                     bg='white', fg='black').pack(pady=(0, 6))
            tk.Frame(grp, bg='#cccccc', height=1).pack(fill='x', pady=(0, 8))
            for text, cmd in btns:
                ttk.Button(grp, text=text, command=cmd,
                           style='Roster.TButton').pack(pady=4)

        # Status bar
        self._sv = tk.StringVar(value='Ready')
        self._status_lbl = tk.Label(self, textvariable=self._sv, bg='#f5f5f5', fg='#555',
                                    font=('Arial',9), anchor='w', padx=12, pady=5, relief='flat')
        self._status_lbl.pack(fill='x', side='bottom')

        self._menubar()

        self.update_idletasks()
        sw,sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w,h   = self.winfo_reqwidth(), self.winfo_reqheight()
        self.geometry(f'+{(sw-w)//2}+{(sh-h)//2}')

    def _header(self):
        tk.Label(self, text="NHL '94  GENS ROSTER TOOL",
                 font=('Arial',22,'bold'), bg='white', fg='#111', pady=30).pack()

    def _toggle_btn(self, parent, text, val):
        b = tk.Button(parent, text=text, width=11,
                      relief='flat', bd=0, font=('Arial',10,'bold'), cursor='hand2',
                      command=lambda v=val: self._set_teams(v))
        b.pack(side='left', padx=3)
        return b


    # ── Menu bar ────────────────────────────────────────────────────

    def _menubar(self):
        bar    = tk.Menu(self)
        file_m = tk.Menu(bar, tearoff=0)
        file_m.add_command(label='Version', command=self._show_version)
        file_m.add_separator()
        file_m.add_command(label='Exit', command=self.destroy)
        bar.add_cascade(label='File', menu=file_m)
        help_m = tk.Menu(bar, tearoff=0)
        help_m.add_command(label='Player Data Instructions', command=self._help_players)
        help_m.add_command(label='Team Data Instructions',   command=self._help_teams)
        bar.add_cascade(label='Help', menu=help_m)
        self.config(menu=bar)

    def _show_version(self):
        w = tk.Toplevel(self)
        w.title('Version Info')
        w.resizable(False, False)
        w.configure(bg='white')
        f = tk.Frame(w, bg='white', padx=36, pady=28)
        f.pack()
        tk.Label(f, text="NHL '94 Roster Tool", font=('Arial', 14, 'bold'), bg='white').pack()
        tk.Label(f, text='Version 1.0.0',                    font=('Arial', 11),     bg='white', fg='#555').pack(pady=(6,0))
        tk.Label(f, text='Released May 2026',                 font=('Arial', 10),     bg='white', fg='#888').pack(pady=(2,0))
        tk.Label(f, text='Supports Sega Genesis (.bin) ROMs', font=('Arial', 10),     bg='white', fg='#888').pack(pady=(2,16))
        ttk.Button(f, text='Close', command=w.destroy).pack()
        w.grab_set()
        w.focus_set()

    _PLAYER_HELP = [
        ('h1', 'Player Data'),
        ('h2', 'How It Works'),
        ('p',  'Export reads all player data from a ROM and saves it as a CSV file you can open and edit in Excel or any spreadsheet app.\n\n'
               'Import reads your edited CSV and writes the player data back into a ROM, saving a new versioned copy (e.g. ROM_v01.bin, ROM_v02.bin).\n\n'
               'The 30/32 Teams toggle must match your ROM before importing.'),
        ('h2', 'Player Order'),
        ('p',  'Within each team, players must appear in this exact order:\n\n'
               '  1. Goalies (G)\n  2. Forwards (F)\n  3. Defense (D)\n\n'
               'Each team must have 1–4 Goalies, 1–15 Forwards, and 1–15 Defense players.'),
        ('h2', 'Name Rules'),
        ('p',  '• First and Last name combined — including the space between them — must not exceed 18 characters total.\n'
               '• Allowed characters: letters, hyphens ( - ), periods ( . ), apostrophes ( \' ).\n'
               '• No numbers or other special characters in player names.'),
        ('h2', 'Column Reference'),
        ('code', 'First, Last     Player first and last name\n'
                 'Abv             Team abbreviation\n'
                 'Pos             G (Goalie)  F (Forward)  D (Defense)\n'
                 'JNo             Jersey number in hex format (00–FF, e.g. 0A, 1F)\n'
                 'Ovr             Overall rating — shown on export, not written on import\n'
                 'Wgt             Weight (0–15)\n'
                 'Hnd             Handedness (0–15)\n'
                 'Agl Spd OfA DfA ShP-PkC Chk StH ShA\n'
                 'End-StR Rgh-StL Pas-GlR Agr-GlL\n'
                 '                Skill attributes — each value 0–6'),
        ('h2', 'Common Errors'),
        ('p',  '"CSV missing columns"\n'
               'Only use CSVs exported by this tool. Do not rename or remove columns.\n\n'
               '"Pos must be G, F, or D"\n'
               'Only these three position codes are accepted.\n\n'
               '"goalies must come before forwards and defense"\n'
               'Re-order rows so all Goalies appear first, then Forwards, then Defense.\n\n'
               '"name is X chars — max 18"\n'
               'Shorten the player\'s first or last name so the total (with space) is 18 or fewer.\n\n'
               '"JNo must be hex 00–FF"\n'
               'Jersey numbers use hexadecimal format (e.g. 0A, 1F, 2C). Use 00–09 for single-digit numbers.\n\n'
               '"needs X bytes, only Y available"\n'
               'Too much player data for this ROM\'s allocated space. Try shortening some long player names.'),
    ]

    _TEAM_HELP = [
        ('h1', 'Team Data'),
        ('h2', 'How It Works'),
        ('p',  'Export reads team names, abbreviations, arena names, and ratings from a ROM and saves them as a CSV.\n\n'
               'Import writes those values back into a ROM, saving a new versioned copy.\n\n'
               'You can import with or without the name columns. If the Arena column is present, city names, abbreviations, team names, and arena names will all be updated. If absent, only the numeric ratings are updated.\n\n'
               'The 30/32 Teams toggle must match your ROM before importing.'),
        ('h2', 'Abbreviation Rules'),
        ('p',  '• Must be 2–3 characters long.\n'
               '• Letters and numbers only — no spaces, hyphens, or special characters.\n'
               '• All abbreviations must be unique (not case-sensitive). No two teams can share the same abbreviation.'),
        ('h2', 'Column Reference'),
        ('code', 'Team City       City name (e.g. Boston)\n'
                 'Abv             Team abbreviation (e.g. BOS)\n'
                 'Team Name       Team name (e.g. Bruins)\n'
                 'Arena           Arena name (e.g. Boston Garden)\n'
                 'Overall         Team overall rating (0–99)\n'
                 'Offense         Offensive strength (0–7)\n'
                 'Defense         Defensive strength (0–7)\n'
                 'PK              Penalty kill strength (0–2)\n'
                 'PP              Power play strength (0–2)\n'
                 'Home            Home ice advantage (0–2)\n'
                 'Road            Road performance (0–3)'),
        ('h2', 'Common Errors'),
        ('p',  '"CSV has X teams — expected Y"\n'
               'The 30/32 toggle doesn\'t match your ROM. Switch it and try again.\n\n'
               '"Team City / Team Name / Arena must not be empty"\n'
               'All three name fields are required when updating team names.\n\n'
               '"Abv must be 2–3 letters/numbers"\n'
               'Check for spaces or special characters in the abbreviation column.\n\n'
               '"Abv is a duplicate"\n'
               'Every team must have a unique abbreviation. Check for repeated values.\n\n'
               '"Overall must be 0–99"\n'
               'Value is out of the allowed range.\n\n'
               '"Offense/Defense must be 0–7"\n'
               'Values must be between 0 and 7.\n\n'
               '"PK/PP must be 0–2"\n'
               'Values must be 0, 1, or 2.\n\n'
               '"Home must be 0–2" / "Road must be 0–3"\n'
               'Values are out of the allowed range for those fields.'),
    ]

    def _help_window(self, title, sections):
        from tkinter import scrolledtext
        w = tk.Toplevel(self)
        w.title(title)
        w.resizable(False, True)
        w.configure(bg='white')
        st = scrolledtext.ScrolledText(w, width=64, height=32, wrap=tk.WORD,
                                       font=('Arial', 10), bg='white', bd=0,
                                       padx=22, pady=18, highlightthickness=0)
        st.tag_configure('h1',   font=('Arial', 13, 'bold'), spacing3=10)
        st.tag_configure('h2',   font=('Arial', 10, 'bold'), spacing1=16, spacing3=4)
        st.tag_configure('p',    spacing3=4)
        st.tag_configure('code', font=('Courier New', 9), foreground='#333',
                         lmargin1=12, lmargin2=12, spacing1=4, spacing3=8)
        for tag, text in sections:
            st.insert('end', text + '\n', tag)
        st.config(state='disabled')
        st.pack(fill='both', expand=True)
        w.grab_set()
        w.focus_set()

    def _help_players(self):
        self._help_window('Player Data Instructions', self._PLAYER_HELP)

    def _help_teams(self):
        self._help_window('Team Data Instructions', self._TEAM_HELP)

    # ────────────────────────────────────────────────────────────────

    def _set_teams(self, val):
        global n_teams
        n_teams = val
        self._nteams = val
        self._refresh_toggle()

    def _refresh_toggle(self):
        on  = dict(bg='#1D4ED8', fg='white', relief='sunken')
        off = dict(bg='#e0e0e0', fg='#555',  relief='flat')
        self._btn30.configure(**(on if self._nteams==30 else off))
        self._btn32.configure(**(on if self._nteams==32 else off))

    def _status(self, msg, error=False):
        self._sv.set(msg)
        self._status_lbl.configure(fg='#c0392b' if error else '#555')
        self.update_idletasks()

    def _err(self, title, exc):
        msg = str(exc)
        self._status(f'Error — {msg}', error=True)
        messagebox.showerror(title, msg)

    def _rom(self, title='Select ROM file'):
        p = filedialog.askopenfilename(title=title,
                filetypes=[('Genesis ROM','*.bin'),('All files','*.*')])
        if not p: return None, None
        with open(p,'rb') as f: return f.read(), p

    def _csv_in(self, title='Select CSV file'):
        p = filedialog.askopenfilename(title=title,
                filetypes=[('CSV','*.csv'),('All files','*.*')])
        if not p: return None, None
        with open(p,'r',encoding='utf-8-sig',newline='') as f: return f.read(), p

    def _csv_out(self, default, initialdir=None):
        return filedialog.asksaveasfilename(defaultextension='.csv',
                initialfile=default, initialdir=initialdir,
                filetypes=[('CSV','*.csv')])

    def _bin_out(self, default, initialdir=None):
        return filedialog.asksaveasfilename(defaultextension='.bin',
                initialfile=default, initialdir=initialdir,
                filetypes=[('Genesis ROM','*.bin')])

    @staticmethod
    def _next_version(dir_, base):
        for n in range(1, 100):
            if not os.path.exists(os.path.join(dir_, f'{base}_v{n:02d}.bin')):
                return f'{base}_v{n:02d}'
        return f'{base}_v99'

    def do_export_players(self):
        rom, path = self._rom('Select ROM to export players from')
        if not rom: return
        try:
            rows = export_players(rom)
        except Exception as e:
            self._err('Player Export — ROM Read Error', e); return
        base = os.path.splitext(os.path.basename(path))[0]
        save = self._csv_out(f'{base}_playerData', initialdir=os.path.dirname(path))
        if not save: return
        try:
            with open(save, 'w', newline='', encoding='utf-8') as f: f.write(rows_to_csv(rows))
        except Exception as e:
            self._err('Player Export — Could Not Save File', e); return
        self._status(f'{len(rows)} players exported → {os.path.basename(save)}')

    def do_import_players(self):
        txt, _ = self._csv_in('Select player CSV')
        if not txt: return
        try:
            rows = csv_to_rows(txt)
        except Exception as e:
            self._err('Player Import — Could Not Read CSV', e); return
        rom, path = self._rom('Select ROM to import players into')
        if not rom: return
        try:
            out = import_players(rom, rows)
        except ValueError as e:
            self._err('Player Import — Validation Error', e); return
        except Exception as e:
            self._err('Player Import — Unexpected Error', e); return
        rom_dir = os.path.dirname(path)
        base = os.path.splitext(os.path.basename(path))[0]
        save = self._bin_out(self._next_version(rom_dir, base), initialdir=rom_dir)
        if not save: return
        try:
            with open(save, 'wb') as f: f.write(out)
        except Exception as e:
            self._err('Player Import — Could Not Save File', e); return
        self._status(f'Players imported → {os.path.basename(save)}')

    def do_export_teams(self):
        rom, path = self._rom('Select ROM to export team data from')
        if not rom: return
        try:
            rows = export_teams(rom)
        except Exception as e:
            self._err('Team Export — ROM Read Error', e); return
        base = os.path.splitext(os.path.basename(path))[0]
        save = self._csv_out(f'{base}_teamData', initialdir=os.path.dirname(path))
        if not save: return
        try:
            with open(save, 'w', newline='', encoding='utf-8') as f: f.write(rows_to_csv(rows))
        except Exception as e:
            self._err('Team Export — Could Not Save File', e); return
        self._status(f'{len(rows)} teams exported → {os.path.basename(save)}')

    def do_import_teams(self):
        txt, _ = self._csv_in('Select team CSV')
        if not txt: return
        try:
            rows = csv_to_rows(txt)
        except Exception as e:
            self._err('Team Import — Could Not Read CSV', e); return
        rom, path = self._rom('Select ROM to import team data into')
        if not rom: return
        try:
            out = import_teams(rom, rows)
        except ValueError as e:
            self._err('Team Import — Validation Error', e); return
        except Exception as e:
            self._err('Team Import — Unexpected Error', e); return
        rom_dir = os.path.dirname(path)
        base = os.path.splitext(os.path.basename(path))[0]
        save = self._bin_out(self._next_version(rom_dir, base), initialdir=rom_dir)
        if not save: return
        try:
            with open(save, 'wb') as f: f.write(out)
        except Exception as e:
            self._err('Team Import — Could Not Save File', e); return
        self._status(f'Team data imported → {os.path.basename(save)}')

if __name__ == '__main__':
    App().mainloop()
