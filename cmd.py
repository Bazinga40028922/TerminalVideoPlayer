import os
import sys
import ctypes

# ==============================================================================
# CORREÇÃO DEFINITIVA DE ARQUITETURA E STRINGS (WinError 193 / SyntaxWarning)
# ==============================================================================
if os.name == 'nt':
    caminhos_vlc = [
        r"C:\Program Files\VideoLAN\VLC",
        r"C:\Program Files (x86)\VideoLAN\VLC",
        os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), r"VideoLAN\VLC"),
        os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), r"VideoLAN\VLC")
    ]
    
    vlc_encontrado = False
    for pasta in caminhos_vlc:
        caminho_dll = os.path.join(pasta, "libvlc.dll")
        if os.path.exists(caminho_dll):
            try:
                # Testa se a DLL é compatível com o seu Python atual (64-bit)
                teste_handle = ctypes.CDLL(caminho_dll)
                del teste_handle 
                
                os.environ['PATH'] = pasta + os.path.pathsep + os.environ['PATH']
                os.add_dll_directory(pasta)
                vlc_encontrado = True
                break
            except OSError:
                # Pula se a DLL for de arquitetura diferente do Python
                continue
                
    # Tentativa de contingência usando a busca padrão do sistema caso as pastas falhem
    if not vlc_encontrado:
        try:
            teste_global = ctypes.CDLL("libvlc.dll")
            del teste_global
            vlc_encontrado = True
        except OSError:
            pass

    if not vlc_encontrado:
        print("\n" + "="*70)
        print("[ERRO DE COMPATIBILIDADE] DLL do VLC correta não encontrada!")
        print("O seu Python atual exige o VLC Media Player de 64 bits.")
        print("Por favor, garanta que instalou a versão (64-bit) do VLC em:")
        print("https://www.videolan.org")
        print("="*70 + "\n")
        sys.exit(1)
# ==============================================================================

import cv2
import time
import numpy as np

try:
    import yt_dlp
    import streamlink
    import vlc
    INTERNET_DISPONIVEL = True
except ImportError:
    INTERNET_DISPONIVEL = False

try:
    import pygame
    PYGAME_DISPONIVEL = True
except ImportError:
    PYGAME_DISPONIVEL = False

# Configuração de inicialização do Windows
if os.name == 'nt':
    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

VIDEO_PADRAO = "YTDown_YouTube_DAN-DA-DAN-Season-1-OP-Opening-8K-60FPS-_Media_-XWFFCcwKuU_001_1080p.mp4"
AUDIO_PADRAO = "YTDown_YouTube_DAN-DA-DAN-Season-1-OP-Opening-8K-60FPS-_Media_-XWFFCcwKuU_009_128k.mp3"
PASTA_PLAYLIST = "playlist"

# 1 = Desenho de Texto (Terminal), 2 = Vídeo Normal HD Janela
MODO_REPRODUCAO = 1 

def obter_tamanho_terminal():
    try:
        colunas, lines = os.get_terminal_size()
        return colunas, lines
    except OSError:
        return 110, 30

def abrir_captura_com_timeout(url_stream):
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "timeout=5000000;reconnect=1;reconnect_streamed=1;reconnect_delay_max=2;nobuffer=1"
    return cv2.VideoCapture(url_stream, cv2.CAP_FFMPEG)

def reproduzir_midia(arquivo_video, arquivo_audio, streaming_internet=False, modo_ultra_peak=False):
    global MODO_REPRODUCAO
    
    if streaming_internet:
        cap = abrir_captura_com_timeout(arquivo_video)
    else:
        cap = cv2.VideoCapture(arquivo_video)

    if not cap.isOpened():
        print(f"\n[ERRO] Não foi possível abrir o fluxo de vídeo.")
        time.sleep(3)
        return False

    cap.set(cv2.CAP_PROP_BUFFERSIZE, 2 if not streaming_internet else 8)

    som_carregado = False
    player_vlc = None

    if arquivo_audio:
        if streaming_internet and INTERNET_DISPONIVEL:
            try:
                instancia_vlc = vlc.Instance("--quiet", "--no-video", "--network-caching=4000")
                player_vlc = instancia_vlc.media_player_new()
                media = instancia_vlc.media_new(arquivo_audio)
                player_vlc.set_media(media)
                som_carregado = True
            except Exception:
                pass
        elif not streaming_internet and PYGAME_DISPONIVEL:
            try:
                pygame.mixer.quit()
            except: pass
            pygame.mixer.init()
            try:
                pygame.mixer.music.load(arquivo_audio)
                som_carregado = True
            except Exception:
                pass

    fps_video = cap.get(cv2.CAP_PROP_FPS)
    if fps_video == 0 or fps_video > 100: fps_video = 60
    tempo_por_frame = 1.0 / fps_video

    # Modo texto maximiza o terminal
    if MODO_REPRODUCAO == 1 and os.name == 'nt':
        hwnd = kernel32.GetConsoleWindow()
        user32.SendMessageW(hwnd, 0x0112, 0xF110, 0) # Maximize console
        sys.stdout.write("\033[?25l\033[2J\033[H")
        sys.stdout.flush()
    elif MODO_REPRODUCAO == 2:
        cv2.namedWindow("Ultra Peak Player HD", cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty("Ultra Peak Player HD", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    if som_carregado:
        if streaming_internet and player_vlc:
            player_vlc.play()
        elif not streaming_internet:
            pygame.mixer.music.play()
    
    time.sleep(1.5) 
    tempo_inicio = time.time()
    tentativas_reconexao = 0

    try:
        while cap.isOpened():
            if som_carregado:
                if streaming_internet and player_vlc:
                    if player_vlc.get_state() in [vlc.State.Ended, vlc.State.Stopped, vlc.State.Error]:
                        break
                    tempo_atual = player_vlc.get_time() / 1000.0
                    if tempo_atual < 0: 
                        if (time.time() - tempo_inicio) > 8: break
                        tempo_atual = time.time() - tempo_inicio
                else:
                    tempo_atual = pygame.mixer.music.get_pos() / 1000.0
                    if tempo_atual < 0: break
            else:
                tempo_atual = time.time() - tempo_inicio

            frame_alvo = int(tempo_atual * fps_video)
            frame_actual = cap.get(cv2.CAP_PROP_POS_FRAMES)

            if frame_alvo > frame_actual:
                for _ in range(int(frame_alvo - frame_actual - 1)):
                    cap.grab()

            ret, frame = cap.read()
            
            if not ret:
                if streaming_internet and player_vlc and player_vlc.get_state() == vlc.State.Ended:
                    break
                if streaming_internet and tentativas_reconexao < 2:
                    tentativas_reconexao += 1
                    time.sleep(0.2)
                    cap.release()
                    cap = abrir_captura_com_timeout(arquivo_video)
                    continue
                else:
                    break

            tentativas_reconexao = 0 

            # MODO 1: RENDERIZAÇÃO EM TEXTO
            if MODO_REPRODUCAO == 1:
                largura_maxima, altura_maxima = obter_tamanho_terminal()
                h_orig, w_orig = frame.shape[:2]
                proporcao = h_orig / w_orig
                
                if modo_ultra_peak:
                    nova_largura = largura_maxima - 1
                else:
                    nova_largura = min(largura_maxima, 75)
                    
                nova_altura = int(nova_largura * proporcao)
                if nova_altura % 2 != 0: nova_altura += 1
                    
                if (nova_altura // 2) > (altura_maxima - 1):
                    nova_altura = (altura_maxima - 1) * 2
                    nova_largura = int(nova_altura / proporcao)

                frame_redimensionado = cv2.resize(frame, (nova_largura, nova_altura))
                rgb = cv2.cvtColor(frame_redimensionado, cv2.COLOR_BGR2RGB)
                
                cima = rgb[0::2, :, :]
                baixo = rgb[1::2, :, :]
                
                r1, g1, b1 = cima[:, :, 0], cima[:, :, 1], cima[:, :, 2]
                r2, g2, b2 = baixo[:, :, 0], baixo[:, :, 1], baixo[:, :, 2]

                linhas = [
                    "".join(
                        f"\033[38;2;{r1[y, x]};{g1[y, x]};{b1[y, x]}m\033[48;2;{r2[y, x]};{g2[y, x]};{b2[y, x]}m▀"
                        for x in range(nova_largura)
                    ) + "\033[0m"
                    for y in range(nova_altura // 2)
                ]
                
                buffer_tela = "\033[H" + "\n".join(linhas) + "\n"
                sys.stdout.write(buffer_tela)
                sys.stdout.flush()

            # MODO 2: REPRODUÇÃO NORMAL DO VÍDEO
            elif MODO_REPRODUCAO == 2:
                cv2.imshow("Ultra Peak Player HD", frame)
                if cv2.waitKey(1) & 0xFF in [27, ord('q'), ord('Q')]:
                    break

            if som_carregado:
                if streaming_internet and player_vlc:
                    tempo_atual_pos = player_vlc.get_time() / 1000.0
                else:
                    tempo_atual_pos = pygame.mixer.music.get_pos() / 1000.0
                
                frame_decorrido = cap.get(cv2.CAP_PROP_POS_FRAMES)
                tempo_espera = (frame_decorrido * tempo_por_frame) - tempo_atual_pos
                if tempo_espera > 0:
                    time.sleep(tempo_espera * 0.9)
            else:
                time.sleep(tempo_por_frame * 0.95)
    finally:
        if som_carregado:
            if player_vlc: player_vlc.stop()
            else:
                pygame.mixer.music.stop()
                pygame.mixer.quit()
        if MODO_REPRODUCAO == 1:
            sys.stdout.write("\033[?25h\033[0m\n")
            sys.stdout.flush()
        elif MODO_REPRODUCAO == 2:
            cv2.destroyAllWindows()
        cap.release()
    return True

def rodar_playlist():
    caminho_atual = os.path.dirname(os.path.abspath(__file__))
    pasta_real = os.path.join(caminho_atual, PASTA_PLAYLIST)
    
    if not os.path.exists(pasta_real):
        os.makedirs(pasta_real)
        print(f"\n[AVISO] Pasta '{PASTA_PLAYLIST}' criada em: {pasta_real}")
        return

    arquivos = os.listdir(pasta_real)
    videos = [f for f in arquivos if f.lower().endswith(('.mp4', '.mkv', '.avi'))]
    videos.sort()

    if not videos:
        print(f"\n[INFO] Nenhum vídeo encontrado dentro de: {pasta_real}")
        time.sleep(3)
        return

    print(f"\n[INFO] Analisando {len(videos)} vídeos na pasta...")
    time.sleep(1)

    for video in videos:
        caminho_video = os.path.join(pasta_real, video)
        termo_busca = video.lower()[:20]
        
        caminho_audio = None
        for arq in arquivos:
            arq_lower = arq.lower()
            if arq_lower.endswith(('.mp3', '.wav', '.m4a', '.ogg')):
                if arq_lower.startswith(termo_busca):
                    caminho_audio = os.path.join(pasta_real, arq)
                    break
        
        reproduzir_midia(caminho_video, caminho_audio, streaming_internet=False, modo_ultra_peak=False)

def rodar_da_internet(url, exibir_msg=True):
    if exibir_msg:
        print("\n[INFO] Extraindo streams estáveis com canal Streamlink...")
    try:
        sessao = streamlink.Streamlink()
        streams = sessao.streams(url)
        
        if 'worst' in streams:
            url_video_stream = streams['worst'].url
        else:
            url_video_stream = list(streams.values())[0].url

        ydl_opts_audio = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True
        }
        with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl_audio:
            info_audio = ydl_audio.extract_info(url, download=False)
            url_audio_stream = info_audio['url']
            
        if exibir_msg:
            print(f"[OK] Streaming ativo.")
            time.sleep(0.5)
        
        reproduzir_midia(url_video_stream, url_audio_stream, streaming_internet=True, modo_ultra_peak=False)
        return True
        
    except Exception as e:
        print(f"\n[ERRO] Falha ao sintonizar a nuvem para {url}: {e}")
        time.sleep(2)
        return False

def rodar_playlist_secreta_animes():
    links_peak = [
        "https://www.youtube.com/watch?v=-XWFFCcwKuU",  # Dandadan OP
        "https://www.youtube.com/watch?v=L96VbQ9ytWk",  # Call of The Night OP
        # "https://www.youtube.com/watch?v=75WraMAZ0Lo"   # My Dress-Up Darling S2 ED (Desable)
    ]
    
    print("\n" + "="*60)
    print("      ATIVANDO COMANDO SECRETO: PLAYLIST ULTRA PEAK ANIME 60FPS! 🔥")
    print("="*60)
    time.sleep(1.0)
    
    for i, link in enumerate(links_peak, 1):
        print(f"\n[PLAYLIST SECRETA] Sintonizando em Alta Performance {i} de {len(links_peak)}...")
        try:
            sessao = streamlink.Streamlink()
            streams = sessao.streams(link)
            
            if '1080p60' in streams:
                url_video_stream = streams['1080p60'].url
            elif '720p60' in streams:
                url_video_stream = streams['720p60'].url
            elif 'best' in streams:
                url_video_stream = streams['best'].url
            else:
                url_video_stream = list(streams.values())[-1].url

            ydl_opts_audio = {
                'format': 'bestaudio/best',
                'quiet': True,
                'no_warnings': True
            }
            with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl_audio:
                info_audio = ydl_audio.extract_info(link, download=False)
                url_audio_stream = info_audio['url']
            
            reproduzir_midia(url_video_stream, url_audio_stream, streaming_internet=True, modo_ultra_peak=True)
            time.sleep(0.5) 
        except Exception as e:
            print(f"\n[ERRO] Falha ao carregar música {i}: {e}")
            time.sleep(2)

if __name__ == "__main__":
    print("="*60)
    print("         TERMINAL VIDEO PLAYER ULTRA PRO STREAMLINK V2")
    print("="*60)
    print("-> Digite 'playlist' para rodar os arquivos locais da pasta.")
    print("-> Cole um link para rodar da web.")
    print("-> Ou aperte [ENTER] para rodar apenas o vídeo padrão local.")
    print("-"*60)
    
    comando = input("Comando ou URL: ").strip()
    
    print("\n" + "-"*60)
    print(" SELECIONE O MODO DE EXIBIÇÃO:")
    print(" [1] Modo Terminal Retro (Desenho com Caracteres)")
    print(" [2] Modo Cinema Cinema (Vídeo Normal Limpo em Alta Definição)")
    print("-"*60)
    
    escolha_modo = input("Escolha o modo (1 ou 2): ").strip()
    if escolha_modo == "2":
        MODO_REPRODUCAO = 2
    else:
        MODO_REPRODUCAO = 1
        
    if comando.lower() == "peak anime":
        rodar_playlist_secreta_animes()
    elif comando.lower() == "playlist":
        rodar_playlist()
    elif comando.startswith(("http://", "https://", "www.")):
        rodar_da_internet(comando)
    else:
        caminho_atual = os.path.dirname(os.path.abspath(__file__))
        v_padrao = os.path.join(caminho_atual, VIDEO_PADRAO)
        a_padrao = os.path.join(caminho_atual, AUDIO_PADRAO)
        reproduzir_midia(v_padrao, a_padrao, streaming_internet=False, modo_ultra_peak=False)
