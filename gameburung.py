import pygame
import sys
import random
import math
import os

# Inisialisasi
pygame.init()
pygame.mixer.init()
lebar, tinggi = 400, 600
layar = pygame.display.set_mode((lebar, tinggi))
pygame.display.set_caption("Flappy Bird Adventure")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 32, bold=True)
font_kecil = pygame.font.SysFont("Arial", 24)

# Warna
BIRU_LANGIT = (135, 206, 235)
HIJAU_PIPA = (0, 160, 0)
KUNING_BURUNG = (255, 215, 0)
ORANYE_PARUH = (255, 165, 0)
PUTIH = (255, 255, 255)
MERAH = (255, 0, 0)
EMAS = (255, 215, 0)

# Efek visual
PARTICLE_COLORS = [(255, 255, 100), (255, 200, 50), (255, 150, 0)]
BACKGROUND_COLORS = [(135, 206, 235), (100, 180, 255), (70, 130, 180)]
current_bg_index = 0
bg_transition_time = 0
bg_transition_duration = 1000  # ms

# Variabel efek getar
shake_intensity = 0
shake_duration = 0
shake_offset = (0, 0)

# Load aset dengan error handling
def load_image(path, default_surface_func=None):
    try:
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            return img
        else:
            raise FileNotFoundError
    except:
        if default_surface_func:
            return default_surface_func()
        return None

def buat_burung_default():
    surface = pygame.Surface((40, 30), pygame.SRCALPHA)
    # Badan burung (elips)
    pygame.draw.ellipse(surface, KUNING_BURUNG, (0, 0, 40, 30))
    # Mata
    pygame.draw.circle(surface, (0, 0, 0), (30, 10), 3)
    pygame.draw.circle(surface, (255, 255, 255), (29, 9), 1)
    # Paruh
    pygame.draw.polygon(surface, ORANYE_PARUH, [(40, 15), (50, 10), (50, 20)])
    # Sayap (akan dianimasikan)
    pygame.draw.ellipse(surface, (200, 150, 0), (5, 15, 20, 10))
    return surface

def buat_pipa_default():
    surface = pygame.Surface((80, 500), pygame.SRCALPHA)
    surface.fill(HIJAU_PIPA)
    # Tambahkan detail pada pipa
    pygame.draw.rect(surface, (0, 140, 0), (0, 0, 80, 30))
    pygame.draw.rect(surface, (0, 140, 0), (0, 470, 80, 30))
    return surface

def buat_background_default():
    surface = pygame.Surface((lebar, tinggi))
    surface.fill(BIRU_LANGIT)
    # Gambar awan sederhana
    for _ in range(5):
        x = random.randint(0, lebar)
        y = random.randint(0, tinggi//2)
        size = random.randint(20, 60)
        pygame.draw.circle(surface, (255, 255, 255), (x, y), size)
        pygame.draw.circle(surface, (255, 255, 255), (x + size//2, y - size//4), size//1.5)
        pygame.draw.circle(surface, (255, 255, 255), (x - size//2, y - size//4), size//1.5)
    return surface

# Load assets
bg = load_image("latar.png", buat_background_default)
if bg:
    bg = pygame.transform.scale(bg, (lebar, tinggi))
else:
    bg = buat_background_default()

burung_img = load_image("burung.png", buat_burung_default)
if burung_img:
    burung_img = pygame.transform.scale(burung_img, (40, 30))
else:
    burung_img = buat_burung_default()

pipa_img = load_image("pipa.png", buat_pipa_default)
if pipa_img:
    pipa_img = pygame.transform.scale(pipa_img, (80, 500))
else:
    pipa_img = buat_pipa_default()

# Load suara dengan error handling
try:
    pygame.mixer.music.load("music.mp3")
    pygame.mixer.music.play(-1)  # loop terus
    pygame.mixer.music.set_volume(0.5)
except:
    print("File musik tidak ditemukan")

try:
    suara_poin = pygame.mixer.Sound("koin.mp3")
    suara_poin.set_volume(0.7)
except:
    suara_poin = None
    print("File suara koin tidak ditemukan")

try:
    suara_lompat = pygame.mixer.Sound("lompat.wav")
    suara_lompat.set_volume(0.5)
except:
    suara_lompat = None
    print("File suara lompat tidak ditemukan")

try:
    suara_tabrak = pygame.mixer.Sound("tabrak.wav")
    suara_tabrak.set_volume(0.7)
except:
    suara_tabrak = None
    print("File suara tabrak tidak ditemukan")

# Game states
MENU = 0
PLAYING = 1
GAME_OVER = 2
game_state = MENU

# Burung
burung = burung_img.get_rect(center=(80, tinggi//2))
gravitasi = 0
lompatan = -8
rotasi = 0
sayap_offset = 0
sayap_direction = 1
animasi_sayap = 0

# Pipa
pipa_list = []
pipa_scored = set()  # Set untuk melacak pipa yang sudah memberikan skor
kecepatan_pipa = 4
jarak_pipa = 200
SPAWNPIPE = pygame.USEREVENT
pygame.time.set_timer(SPAWNPIPE, 1500)

# Efek partikel
partikel_list = []

# Skor
skor = 0
high_score = 0
score_effect = {"value": 0, "pos": (0, 0), "timer": 0, "active": False}

def buat_pipa():
    tinggi_acak = random.randint(200, 400)
    pipa_bawah = pipa_img.get_rect(midtop=(lebar+50, tinggi_acak))
    pipa_atas = pipa_img.get_rect(midbottom=(lebar+50, tinggi_acak - jarak_pipa))
    return pipa_bawah, pipa_atas

def gambar_pipa(pipa_list):
    for pipa in pipa_list:
        if pipa.bottom >= tinggi:  # pipa bawah
            layar.blit(pipa_img, pipa)
        else:  # pipa atas (dibalik)
            flip = pygame.transform.flip(pipa_img, False, True)
            layar.blit(flip, pipa)

def buat_partikel(pos, jumlah=10, warna=None):
    if warna is None:
        warna = random.choice(PARTICLE_COLORS)
    for _ in range(jumlah):
        partikel_list.append({
            'pos': list(pos),
            'velocity': [random.uniform(-2, 2), random.uniform(-3, -1)],
            'timer': random.randint(15, 25),
            'color': warna,
            'size': random.randint(2, 5)
        })

def update_partikel():
    for partikel in partikel_list[:]:
        partikel['pos'][0] += partikel['velocity'][0]
        partikel['pos'][1] += partikel['velocity'][1]
        partikel['timer'] -= 1
        partikel['velocity'][1] += 0.1  # Gravitasi untuk partikel
        
        if partikel['timer'] <= 0:
            partikel_list.remove(partikel)

def gambar_partikel():
    for partikel in partikel_list:
        alpha = min(255, partikel['timer'] * 10)
        color = partikel['color'] + (alpha,)
        surf = pygame.Surface((partikel['size'], partikel['size']), pygame.SRCALPHA)
        pygame.draw.circle(surf, color, (partikel['size']//2, partikel['size']//2), partikel['size']//2)
        layar.blit(surf, (int(partikel['pos'][0]), int(partikel['pos'][1])))

def tampilkan_skor():
    # Skor utama
    teks = font.render(f"{skor}", True, PUTIH)
    teks_shadow = font.render(f"{skor}", True, (0, 0, 0))
    layar.blit(teks_shadow, (lebar//2 - teks.get_width()//2 + 2, 52))
    layar.blit(teks, (lebar//2 - teks.get_width()//2, 50))
    
    # Efek skor bertambah
    if score_effect["active"]:
        alpha = min(255, score_effect["timer"] * 12)
        score_text = font_kecil.render(f"+1", True, EMAS)
        score_text.set_alpha(alpha)
        layar.blit(score_text, (score_effect["pos"][0], score_effect["pos"][1] - score_effect["timer"]))
        score_effect["timer"] += 1
        if alpha <= 0:
            score_effect["active"] = False

def tampilkan_menu():
    # Judul dengan efek shadow
    judul = font.render("FLAPPY BIRD", True, PUTIH)
    judul_shadow = font.render("FLAPPY BIRD", True, (0, 0, 0))
    layar.blit(judul_shadow, (lebar//2 - judul.get_width()//2 + 2, tinggi//3 + 2))
    layar.blit(judul, (lebar//2 - judul.get_width()//2, tinggi//3))
    
    # High score
    if high_score > 0:
        hs_text = font_kecil.render(f"High Score: {high_score}", True, EMAS)
        hs_shadow = font_kecil.render(f"High Score: {high_score}", True, (0, 0, 0))
        layar.blit(hs_shadow, (lebar//2 - hs_text.get_width()//2 + 1, tinggi//2 - 40))
        layar.blit(hs_text, (lebar//2 - hs_text.get_width()//2, tinggi//2 - 41))
    
    # Instruksi
    instruksi = font_kecil.render("Tekan SPACE untuk mulai", True, PUTIH)
    instruksi_shadow = font_kecil.render("Tekan SPACE untuk mulai", True, (0, 0, 0))
    layar.blit(instruksi_shadow, (lebar//2 - instruksi.get_width()//2 + 1, tinggi//2 + 1))
    layar.blit(instruksi, (lebar//2 - instruksi.get_width()//2, tinggi//2))
    
    # Flashing instruction
    if pygame.time.get_ticks() % 1000 < 500:
        start_hint = font_kecil.render("↑ Tekan SPACE untuk terbang", True, PUTIH)
        layar.blit(start_hint, (lebar//2 - start_hint.get_width()//2, tinggi//2 + 40))

def tampilkan_game_over():
    # Game over text
    game_over_text = font.render("GAME OVER", True, MERAH)
    game_over_shadow = font.render("GAME OVER", True, (0, 0, 0))
    layar.blit(game_over_shadow, (lebar//2 - game_over_text.get_width()//2 + 2, tinggi//3 + 2))
    layar.blit(game_over_text, (lebar//2 - game_over_text.get_width()//2, tinggi//3))
    
    # Score
    skor_text = font.render(f"Skor: {skor}", True, PUTIH)
    skor_shadow = font.render(f"Skor: {skor}", True, (0, 0, 0))
    layar.blit(skor_shadow, (lebar//2 - skor_text.get_width()//2 + 1, tinggi//2 + 1))
    layar.blit(skor_text, (lebar//2 - skor_text.get_width()//2, tinggi//2))
    
    # High score
    high_score_text = font.render(f"High Score: {high_score}", True, EMAS)
    high_score_shadow = font.render(f"High Score: {high_score}", True, (0, 0, 0))
    layar.blit(high_score_shadow, (lebar//2 - high_score_text.get_width()//2 + 1, tinggi//2 + 41))
    layar.blit(high_score_text, (lebar//2 - high_score_text.get_width()//2, tinggi//2 + 40))
    
    # Restart instruction
    restart_text = font_kecil.render("Tekan R untuk restart", True, PUTIH)
    restart_shadow = font_kecil.render("Tekan R untuk restart", True, (0, 0, 0))
    layar.blit(restart_shadow, (lebar//2 - restart_text.get_width()//2 + 1, tinggi//2 + 101))
    layar.blit(restart_text, (lebar//2 - restart_text.get_width()//2, tinggi//2 + 100))

def reset_game():
    global burung, gravitasi, pipa_list, skor, game_state, rotasi, pipa_scored, current_bg_index, kecepatan_pipa
    burung.center = (80, tinggi//2)
    gravitasi = 0
    rotasi = 0
    pipa_list.clear()
    pipa_scored.clear()
    partikel_list.clear()
    skor = 0
    game_state = PLAYING
    current_bg_index = (current_bg_index + 1) % len(BACKGROUND_COLORS)
    bg_transition_time = pygame.time.get_ticks()
    kecepatan_pipa = 4  # Reset kecepatan pipa

def trigger_screen_shake(intensity=10, duration=200):
    global shake_intensity, shake_duration
    shake_intensity = intensity
    shake_duration = duration

def apply_screen_shake():
    global shake_duration, shake_offset
    if shake_duration > 0:
        offset_x = random.randint(-shake_intensity, shake_intensity)
        offset_y = random.randint(-shake_intensity, shake_intensity)
        shake_duration -= clock.get_time()
        shake_offset = (offset_x, offset_y)
        return (offset_x, offset_y)
    shake_offset = (0, 0)
    return (0, 0)

# Loop game
while True:
    dt = clock.tick(60) / 1000  # Delta time in seconds
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            
        if game_state == MENU:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                game_state = PLAYING
                bg_transition_time = pygame.time.get_ticks()
                
        elif game_state == PLAYING:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                gravitasi = lompatan
                buat_partikel((burung.centerx, burung.bottom))
                rotasi = 20  # Rotasi ke atas saat lompat
                if suara_lompat:
                    suara_lompat.play()
                
            if event.type == SPAWNPIPE:
                pipa_list.extend(buat_pipa())
                
        elif game_state == GAME_OVER:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                reset_game()

    # Gambar background dengan efek transisi
    current_time = pygame.time.get_ticks()
    if current_time - bg_transition_time < bg_transition_duration:
        # Interpolasi antara warna latar belakang
        progress = (current_time - bg_transition_time) / bg_transition_duration
        next_bg_index = (current_bg_index + 1) % len(BACKGROUND_COLORS)
        current_color = BACKGROUND_COLORS[current_bg_index]
        next_color = BACKGROUND_COLORS[next_bg_index]
        
        r = int(current_color[0] + (next_color[0] - current_color[0]) * progress)
        g = int(current_color[1] + (next_color[1] - current_color[1]) * progress)
        b = int(current_color[2] + (next_color[2] - current_color[2]) * progress)
        
        bg_surface = pygame.Surface((lebar, tinggi))
        bg_surface.fill((r, g, b))
        layar.blit(bg_surface, (0, 0))
    else:
        bg_surface = pygame.Surface((lebar, tinggi))
        bg_surface.fill(BACKGROUND_COLORS[current_bg_index])
        layar.blit(bg_surface, (0, 0))
    
    # Apply screen shake offset
    shake_offset = apply_screen_shake()
    
    # Update partikel
    update_partikel()
    gambar_partikel()
    
    if game_state == MENU:
        # Animasi burung di menu
        burung.centery += math.sin(pygame.time.get_ticks() * 0.002) * 1.5
        animasi_sayap = (animasi_sayap + 0.2) % 20
        sayap_angle = math.sin(animasi_sayap) * 15
        burung_rotated = pygame.transform.rotate(burung_img, 10 * math.sin(pygame.time.get_ticks() * 0.003) + sayap_angle)
        layar.blit(burung_rotated, burung_rotated.get_rect(center=burung.center).move(shake_offset))
        tampilkan_menu()
        
    elif game_state == PLAYING:
        # Burung
        gravitasi += 0.5
        burung.centery += gravitasi
        
        # Rotasi burung berdasarkan gravitasi
        rotasi = max(-30, rotasi - 1)  # Batasi rotasi ke bawah
        
        # Animasi sayap
        animasi_sayap = (animasi_sayap + 0.3) % 20
        sayap_angle = math.sin(animasi_sayap) * 15
        
        # Hapus pipa yang sudah lewat layar
        pipa_list = [p for p in pipa_list if p.right > -50]
        
        # Pipa
        for p in pipa_list:
            p.x -= kecepatan_pipa
        
        # Cek tabrakan
        tabrakan = False
        for p in pipa_list:
            if burung.colliderect(p):
                tabrakan = True
                break
        
        if tabrakan or burung.top <= 0 or burung.bottom >= tinggi:
            game_state = GAME_OVER
            high_score = max(high_score, skor)
            buat_partikel(burung.center, 20, MERAH)
            trigger_screen_shake(15, 300)
            if suara_tabrak:
                suara_tabrak.play()
        
        # Cek skor - SISTEM SKOR DIPERBAIKI
        for p in pipa_list:
            # Hanya periksa pipa bawah dan pastikan kita belum memberikan skor untuk pipa ini
            if p.bottom >= tinggi and p.right < burung.left and id(p) not in pipa_scored:
                skor += 1
                pipa_scored.add(id(p))
                score_effect["active"] = True
                score_effect["pos"] = (p.centerx, p.centery)
                score_effect["timer"] = 0
                if suara_poin:
                    suara_poin.play()
                # Setiap 5 poin, tingkatkan kesulitan
                if skor % 5 == 0:
                    kecepatan_pipa += 0.5
                    current_bg_index = (current_bg_index + 1) % len(BACKGROUND_COLORS)
                    bg_transition_time = pygame.time.get_ticks()
        
        # Gambar pipa
        gambar_pipa(pipa_list)
        
        # Gambar burung dengan rotasi dan animasi sayap
        burung_rotated = pygame.transform.rotate(burung_img, rotasi + sayap_angle)
        layar.blit(burung_rotated, burung_rotated.get_rect(center=burung.center).move(shake_offset))
        
        # Tampilkan skor
        tampilkan_skor()
        
    elif game_state == GAME_OVER:
        # Gambar pipa yang tersisa
        gambar_pipa(pipa_list)
        
        # Gambar burung
        burung_rotated = pygame.transform.rotate(burung_img, rotasi)
        layar.blit(burung_rotated, burung_rotated.get_rect(center=burung.center).move(shake_offset))
        
        # Gambar partikel
        gambar_partikel()
        
        tampilkan_game_over()
    
    pygame.display.update()
