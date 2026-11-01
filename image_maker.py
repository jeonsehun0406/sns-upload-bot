"""카드뉴스 이미지 생성 (서버용 - Linux/Render 호환)"""

import os
import io
import re
import requests
import random as _rng
from datetime import date as _date
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from pathlib import Path
from config import APP_NAME, OUTPUT_DIR, FONTS_DIR

TMPL_W, TMPL_H = 1080, 1350
CX = TMPL_W // 2

WHITE       = (255, 255, 255)
BLACK       = (18,  12,  8)
GRAY        = (130, 122, 114)
LGRAY       = (218, 210, 202)
PG_BG       = (236, 230, 224)
HDR_BG      = (24,  12,  5)
HDR_FG      = (255, 248, 235)
HDR_ACC     = (210, 160, 90)
CARD_BG     = (255, 255, 255)
CARD_BD     = (220, 212, 204)
TXT_H       = (18,  12,  8)
TXT_B       = (50,  42,  36)
TXT_S       = (110, 100, 90)
ACCENT      = (196, 88,  38)
TAG_BG      = (255, 244, 236)
PROMO_BG1   = (18,  10,  4)
PROMO_GOLD  = (210, 168, 82)
PROMO_CREAM = (255, 248, 230)

HDR_H = 96
FTR_H = 68
CARD_M = 28
CARD_L = CARD_M
CARD_R = TMPL_W - CARD_M
CARD_T = HDR_H + 20
CARD_B = TMPL_H - FTR_H - 16
CARD_RI = 24
PAD = 44
IL = CARD_L + PAD
IR = CARD_R - PAD
IW = IR - IL
AI_W = 656
AI_H = 868
AI_X = CX - AI_W // 2


# ── 폰트 (서버/로컬 공용) ────────────────────────────────
_NANUM_URL = (
    "https://cdn.jsdelivr.net/gh/naver/nanumfont@master/fonts/NanumGothic.ttf"
)
_NANUM_BOLD_URL = (
    "https://cdn.jsdelivr.net/gh/naver/nanumfont@master/fonts/NanumGothicBold.ttf"
)

def _ensure_font(bold: bool) -> Path:
    fname  = "NanumGothicBold.ttf" if bold else "NanumGothic.ttf"
    fpath  = FONTS_DIR / fname
    if fpath.exists():
        return fpath
    FONTS_DIR.mkdir(exist_ok=True)
    url = _NANUM_BOLD_URL if bold else _NANUM_URL
    try:
        print(f"[image_maker] 폰트 다운로드: {fname}")
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        fpath.write_bytes(r.content)
        print(f"[image_maker] 폰트 저장 완료: {fpath}")
    except Exception as e:
        print(f"[image_maker] 폰트 다운로드 실패({e}), 기본 폰트 사용")
        return None
    return fpath

def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        FONTS_DIR / ("Maplestory Bold.ttf" if bold else "Maplestory Light.ttf"),
        FONTS_DIR / ("NanumGothicBold.ttf" if bold else "NanumGothic.ttf"),
        Path("/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf" if bold
             else "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"),
        Path("C:/Windows/Fonts/" + ("malgunbd.ttf" if bold else "malgun.ttf")),
    ]
    for p in candidates:
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except Exception:
                pass
    # 자동 다운로드
    dl = _ensure_font(bold)
    if dl and dl.exists():
        try:
            return ImageFont.truetype(str(dl), size)
        except Exception:
            pass
    return ImageFont.load_default()

_font_safe = _font  # 서버에서는 동일 폰트 사용


# ── 텍스트 유틸 ───────────────────────────────────────────
def _tw(draw, text, font):
    b = draw.textbbox((0, 0), text, font=font)
    return b[2] - b[0]

def _wrap(draw, text, font, max_w) -> list:
    lines = []
    for para in text.split("\n"):
        if not para.strip():
            lines.append("")
            continue
        cur = ""
        for ch in para:
            test = cur + ch
            if _tw(draw, test, font) > max_w and cur:
                lines.append(cur)
                cur = ch
            else:
                cur = test
        if cur:
            lines.append(cur)
    return lines

def _draw_text_center(draw, text, font, cx, y, max_w, color, gap=10) -> int:
    lh = font.size + gap
    for ln in _wrap(draw, text, font, max_w):
        if not ln:
            y += lh // 2
        else:
            w = _tw(draw, ln, font)
            draw.text((cx - w // 2, y), ln, font=font, fill=color)
            y += lh
    return y

def _clean_text(text: str) -> str:
    return re.sub(r'[\U00010000-\U0010FFFF\u2600-\u27FF]', '', text)


# ── 배경/헤더/푸터 ────────────────────────────────────────
def _make_bg():
    return Image.new("RGB", (TMPL_W, TMPL_H), PG_BG)

def _draw_header(img, badge=""):
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, TMPL_W, HDR_H], fill=HDR_BG)
    draw.line([(0, HDR_H - 1), (TMPL_W, HDR_H - 1)], fill=HDR_ACC, width=2)
    f_b = _font(40, bold=True)
    draw.text((44, 26), "운명의문", font=f_b, fill=HDR_FG)
    f_s = _font(20)
    draw.text((46, 68), "사주 · 타로 · 운세", font=f_s, fill=(180, 162, 135))
    if badge:
        f_badge = _font(26, bold=True)
        bpw = _tw(draw, badge, f_badge) + 28
        bph = 38
        bpx = TMPL_W - bpw - 28
        bpy = (HDR_H - bph) // 2
        draw.rounded_rectangle([bpx, bpy, bpx+bpw, bpy+bph], radius=8,
                                fill=(48, 30, 14), outline=HDR_ACC, width=1)
        draw.text((bpx + 14, bpy + 6), badge, font=f_badge, fill=HDR_ACC)
    return draw

def _draw_card(draw):
    shadow = (210, 202, 194)
    draw.rounded_rectangle([CARD_L+4, CARD_T+4, CARD_R+4, CARD_B+4],
                            radius=CARD_RI, fill=shadow)
    draw.rounded_rectangle([CARD_L, CARD_T, CARD_R, CARD_B],
                            radius=CARD_RI, fill=CARD_BG, outline=CARD_BD, width=1)

def _draw_footer(draw):
    fy = TMPL_H - FTR_H
    draw.rectangle([0, fy, TMPL_W, TMPL_H], fill=HDR_BG)
    draw.line([(0, fy), (TMPL_W, fy)], fill=(40, 24, 10), width=1)
    f_f = _font(24)
    for text, x in [("♥  좋아요", 56), ("댓글", 320), ("공유", 500)]:
        draw.text((x, fy + 22), text, font=f_f, fill=(160, 148, 128))


# ── fal.ai 이미지 생성 ────────────────────────────────────
def _fal_image(prompt: str, w: int, h: int) -> Image.Image:
    fal_key = os.environ.get("FAL_KEY", "")
    if not fal_key:
        return _gradient_fallback(w, h)
    try:
        import fal_client
        result = fal_client.run(
            "fal-ai/flux/schnell",
            arguments={"prompt": prompt, "image_size": "square_hd",
                        "num_inference_steps": 4, "num_images": 1,
                        "enable_safety_checker": False},
        )
        url  = result["images"][0]["url"]
        resp = requests.get(url, timeout=30)
        raw  = Image.open(io.BytesIO(resp.content)).convert("RGB")
        raw  = raw.resize((w, h), Image.LANCZOS)
        return ImageEnhance.Brightness(raw).enhance(0.92)
    except Exception as e:
        print(f"[image_maker] fal.ai 실패({e}), 그라디언트 대체")
        return _gradient_fallback(w, h)

def _gradient_fallback(w, h) -> Image.Image:
    img = Image.new("RGB", (w, h))
    d   = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        d.line([(0, y), (w, y)], fill=(
            int(80*(1-t) + 40*t), int(50*(1-t) + 20*t), int(30*(1-t) + 10*t)
        ))
    return img

def _title_to_image_prompt(title: str) -> str:
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return ""
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=(
                f"다음 한국어 제목의 감정·분위기를 표현하는 fal.ai FLUX용 영어 이미지 프롬프트를 작성해줘.\n"
                f"제목: {title}\n\n"
                f"조건: 영어만, 30단어 이내, no text no people no faces, "
                f"warm rose gold tones elegant cinematic, high quality\n\n영어 프롬프트만 출력:"
            ),
        )
        return resp.text.strip().strip('"').strip("'")
    except Exception as e:
        print(f"[image_maker] Gemini 프롬프트 실패({e})")
        return ""


# ── 카드 1: 제목 + AI 이미지 ─────────────────────────────
def make_title_card(content: dict, topic_img: Image.Image, post_idx: int) -> str:
    img   = _make_bg()
    draw  = _draw_header(img)
    _draw_card(draw)
    _draw_footer(draw)

    title    = content.get("display_title", "")
    category = content.get("category", content.get("content_type", ""))
    promo    = content.get("promo_hook", "")
    inner_top = CARD_T + 28

    if category:
        f_tag = _font(22, bold=True)
        tag   = f"  {category}  "
        tw2   = _tw(draw, tag, f_tag)
        th    = 34
        draw.rounded_rectangle([IL, inner_top, IL+tw2, inner_top+th],
                                radius=17, fill=TAG_BG, outline=ACCENT, width=1)
        draw.text((IL+1, inner_top+6), tag, font=f_tag, fill=ACCENT)
        inner_top += th + 16

    font_size = 40
    while font_size >= 26:
        f_title = _font(font_size, bold=True)
        if _tw(draw, title, f_title) <= IW:
            break
        font_size -= 2
    lines = _wrap(draw, title, f_title, IW)[:2]
    ty    = inner_top
    for ln in lines:
        draw.text((IL, ty), ln, font=f_title, fill=TXT_H)
        ty += font_size + 10

    sep_y = ty + 16
    draw.line([(IL, sep_y), (IR, sep_y)], fill=LGRAY, width=1)

    ai_y    = sep_y + 18
    topic_r = topic_img.resize((AI_W, AI_H), Image.LANCZOS)
    img.paste(topic_r, (AI_X, ai_y))
    draw    = ImageDraw.Draw(img)

    text_y = ai_y + AI_H + 18
    if promo and text_y + 36 < CARD_B - 50:
        f_promo = _font(26)
        pw      = _tw(draw, promo, f_promo)
        draw.text((CX - pw // 2, text_y), promo, font=f_promo, fill=TXT_B)
        text_y += 40

    if text_y + 30 < CARD_B - 40:
        draw.line([(IL+80, text_y), (IR-80, text_y)], fill=LGRAY, width=1)
        text_y += 14
        f_hint = _font(24)
        hint   = "▶  스와이프해서 전체 보기"
        hw     = _tw(draw, hint, f_hint)
        draw.text((CX - hw // 2, text_y), hint, font=f_hint, fill=TXT_S)

    OUTPUT_DIR.mkdir(exist_ok=True)
    path = str(OUTPUT_DIR / f"post_{post_idx:03d}_01_title.jpg")
    img.save(path, "JPEG", quality=95)
    return path


# ── 카드 2~N: 본문 ────────────────────────────────────────
def make_content_card(slide_text: str, card_idx: int, total_cards: int, post_idx: int) -> str:
    img  = _make_bg()
    draw = _draw_header(img, f"{card_idx+1} / {total_cards}")
    _draw_card(draw)
    _draw_footer(draw)

    hdr_top = CARD_T + 26
    av_r    = 28
    av_cx   = IL + av_r
    av_cy   = hdr_top + av_r
    draw.ellipse([av_cx-av_r, av_cy-av_r, av_cx+av_r, av_cy+av_r], fill=HDR_BG)
    draw.ellipse([av_cx-av_r+2, av_cy-av_r+2, av_cx+av_r-2, av_cy+av_r-2],
                 outline=HDR_ACC, width=1)
    f_av  = _font(22, bold=True)
    av_w  = _tw(draw, "운", f_av)
    draw.text((av_cx - av_w//2, av_cy - 14), "운", font=f_av, fill=HDR_ACC)

    name_x = av_cx + av_r + 14
    draw.text((name_x, hdr_top + 2),  "운명의문",     font=_font(26, bold=True), fill=TXT_H)
    today  = _date.today().strftime("%Y.%m.%d")
    draw.text((name_x, hdr_top + 32), f"오늘의운세  ·  {today}", font=_font(20), fill=TXT_S)

    f_num  = _font(22, bold=True)
    num_t  = f"{card_idx+1} / {total_cards}"
    nw     = _tw(draw, num_t, f_num)
    draw.rounded_rectangle([IR-nw-22, hdr_top+6, IR, hdr_top+38], radius=8, fill=(240,234,228))
    draw.text((IR-nw-11, hdr_top+10), num_t, font=f_num, fill=TXT_S)

    div_y = hdr_top + av_r * 2 + 20
    draw.line([(IL, div_y), (IR, div_y)], fill=LGRAY, width=1)

    text_zone_top = div_y + 28
    text_zone_bot = CARD_B - 118

    f_body    = _font(50)
    clean_txt = _clean_text(slide_text)
    lines     = _wrap(draw, clean_txt, f_body, IW)
    lh        = 50 + 28
    empty_lh  = lh // 2

    r2 = _rng.Random(post_idx * 100 + card_idx)
    for _ in range(24):
        sx = r2.randint(IL+10, IR-10)
        sy = r2.randint(text_zone_top+10, text_zone_bot-10)
        sr = r2.choice([1, 1, 2, 2, 3])
        draw.ellipse([sx-sr, sy-sr, sx+sr, sy+sr],
                     fill=r2.choice([(215,205,192),(225,215,202),(205,196,185)]))

    bdg_y   = text_zone_top + 28
    bdg_h   = 52
    f_bdg   = _font(26, bold=True)
    bdg_txt = f"SLIDE  {card_idx+2:02d}"
    bdg_w   = _tw(draw, bdg_txt, f_bdg) + 44
    draw.rounded_rectangle([IL, bdg_y, IL+bdg_w, bdg_y+bdg_h],
                            radius=26, fill=TAG_BG, outline=ACCENT, width=2)
    draw.text((IL+22, bdg_y+13), bdg_txt, font=f_bdg, fill=ACCENT)

    text_y  = bdg_y + bdg_h + 38
    acc_bot = text_y + sum(lh if ln else empty_lh for ln in lines) + 12
    draw.rectangle([IL-10, text_y-12, IL-5, acc_bot], fill=ACCENT)

    for ln in lines:
        if not ln:
            text_y += empty_lh
        else:
            draw.text((IL, text_y), ln, font=f_body, fill=TXT_H)
            text_y += lh

    eng_y = CARD_B - 100
    draw.line([(IL, eng_y), (IR, eng_y)], fill=LGRAY, width=1)
    eng_y += 18
    seed  = post_idx * 11 + card_idx
    likes = 1100 + (seed * 137 % 900)
    cmts  = 60  + (seed * 53  % 140)
    f_eng = _font(24)
    for txt, x in [(f"♥  {likes:,}", IL), (f"◎  {cmts}", IL+280), ("→  공유하기", IL+500)]:
        draw.text((x, eng_y), txt, font=f_eng, fill=(148,136,118))

    OUTPUT_DIR.mkdir(exist_ok=True)
    path = str(OUTPUT_DIR / f"post_{post_idx:03d}_{card_idx+2:02d}_content.jpg")
    img.save(path, "JPEG", quality=95)
    return path


# ── 참여유도 카드 ─────────────────────────────────────────
def make_vote_card(content: dict, card_idx: int, post_idx: int) -> str:
    img   = _make_bg()
    draw  = _draw_header(img, f"{card_idx+1}")
    _draw_card(draw)
    _draw_footer(draw)

    q      = _clean_text(content.get("engagement_q", "어떻게 생각하세요?"))
    side_a = _clean_text(content.get("side_a", "공감해"))
    side_b = _clean_text(content.get("side_b", "아님"))
    f_q    = _font(46, bold=True)
    f_vs   = _font(38, bold=True)
    f_lbl  = _font(24)
    f_sub  = _font(30)

    q_lines  = _wrap(draw, q, f_q, IW)
    q_block_h = len(q_lines) * 60
    btn_h    = 110
    total_h  = 34 + 24 + q_block_h + 32 + 1 + 36 + btn_h + 40 + 1 + 22 + 40
    cy       = max((CARD_B - CARD_T - total_h) // 2 + CARD_T, CARD_T + 50)

    lbl = "이 글을 읽은 당신에게 묻습니다"
    lw2 = _tw(draw, lbl, f_lbl)
    draw.text((CX - lw2 // 2, cy), lbl, font=f_lbl, fill=TXT_S)
    cy += 58

    for ln in q_lines:
        w = _tw(draw, ln, f_q)
        draw.text((CX - w // 2, cy), ln, font=f_q, fill=TXT_H)
        cy += 60
    cy += 32

    draw.line([(IL+40, cy), (IR-40, cy)], fill=LGRAY, width=1)
    cy += 37

    btn_w = 330
    gap   = 24
    lx    = CX - btn_w - gap // 2
    rx    = CX + gap // 2
    draw.rounded_rectangle([lx, cy, lx+btn_w, cy+btn_h], radius=16, fill=(188, 62, 62))
    draw.rounded_rectangle([rx, cy, rx+btn_w, cy+btn_h], radius=16, fill=(50, 90, 168))
    aw  = _tw(draw, side_a, f_vs)
    bw2 = _tw(draw, side_b, f_vs)
    draw.text((lx+(btn_w-aw)//2,  cy+(btn_h-38)//2), side_a, font=f_vs, fill=WHITE)
    draw.text((rx+(btn_w-bw2)//2, cy+(btn_h-38)//2), side_b, font=f_vs, fill=WHITE)
    vsw = _tw(draw, "VS", _font(34, bold=True))
    draw.text((CX - vsw//2, cy+(btn_h-34)//2), "VS", font=_font(34, bold=True), fill=(150,140,128))
    cy += btn_h + 40

    draw.line([(IL+40, cy), (IR-40, cy)], fill=LGRAY, width=1)
    cy += 23
    sub = "댓글로 의견 남겨주세요!"
    sw  = _tw(draw, sub, f_sub)
    draw.text((CX - sw // 2, cy), sub, font=f_sub, fill=TXT_S)

    OUTPUT_DIR.mkdir(exist_ok=True)
    path = str(OUTPUT_DIR / f"post_{post_idx:03d}_{card_idx+2:02d}_vote.jpg")
    img.save(path, "JPEG", quality=95)
    return path


# ── 마지막 카드: 브랜드 CTA ───────────────────────────────
def make_closing_card(post_idx: int, card_num: int) -> str:
    img  = Image.new("RGB", (TMPL_W, TMPL_H), PROMO_BG1)
    draw = ImageDraw.Draw(img)
    r1, g1, b1 = PROMO_BG1
    r2, g2, b2 = (62, 30, 8)
    for y in range(TMPL_H):
        t = y / TMPL_H
        draw.line([(0, y), (TMPL_W, y)], fill=(
            int(r1*(1-t)+r2*t), int(g1*(1-t)+g2*t), int(b1*(1-t)+b2*t)
        ))

    glow = Image.new("RGBA", (TMPL_W, TMPL_H), (0,0,0,0))
    gd   = ImageDraw.Draw(glow)
    gcx, gcy = TMPL_W // 2, TMPL_H // 2 - 80
    for radius in range(480, 0, -6):
        alpha = int(16 * (1 - radius / 480))
        gd.ellipse([gcx-radius, gcy-radius, gcx+radius, gcy+radius],
                   fill=(195, 140, 52, alpha))
    img_rgba = img.convert("RGBA")
    img_rgba.alpha_composite(glow)
    img  = img_rgba.convert("RGB")
    draw = ImageDraw.Draw(img)

    m = 38
    draw.rectangle([m, m, TMPL_W-m, TMPL_H-m], outline=PROMO_GOLD, width=2)

    cy = 178
    f_tag = _font(24, bold=True)
    tag   = "  사주 · 타로 · 운세  "
    tw2   = _tw(draw, tag, f_tag)
    tx    = CX - tw2 // 2
    draw.rounded_rectangle([tx-4, cy, tx+tw2+4, cy+44], radius=22,
                            fill=(45, 25, 8), outline=PROMO_GOLD, width=2)
    draw.text((tx, cy+10), tag, font=f_tag, fill=PROMO_GOLD)
    cy += 80

    f_main = _font(96, bold=True)
    brand  = "운명의문"
    mw     = _tw(draw, brand, f_main)
    for ox, oy, sc in [(4, 5, 0.15), (2, 3, 0.3), (1, 2, 0.5)]:
        shadow_c = (int(PROMO_GOLD[0]*sc), int(PROMO_GOLD[1]*sc*0.8), int(PROMO_GOLD[2]*sc*0.2))
        draw.text((CX - mw//2 + ox, cy + oy), brand, font=f_main, fill=shadow_c)
    draw.text((CX - mw // 2, cy), brand, font=f_main, fill=PROMO_CREAM)
    cy += 120

    lw = 220
    draw.line([(CX-lw, cy), (CX+lw, cy)], fill=PROMO_GOLD, width=2)
    cy += 46

    f_slogan = _font(30)
    slogan   = "당신의 운명, 지금 확인하세요"
    sw2      = _tw(draw, slogan, f_slogan)
    draw.text((CX - sw2 // 2, cy), slogan, font=f_slogan, fill=(215, 196, 160))
    cy += 80

    features = ["AI 사주 분석", "타로 카드 리딩", "오늘의 운세 · 궁합"]
    f_feat   = _font(30)
    for feat in features:
        fw2 = _tw(draw, f"◆  {feat}", f_feat)
        draw.text((CX - fw2 // 2, cy), f"◆  {feat}", font=f_feat, fill=(218, 200, 168))
        cy += 54
    cy += 44

    btn_w2, btn_h2 = 620, 96
    bx = CX - btn_w2 // 2
    draw.rounded_rectangle([bx+3, cy+4, bx+btn_w2+3, cy+btn_h2+4], radius=48, fill=(65,42,10))
    GOLD_BTN = (232, 188, 88)
    draw.rounded_rectangle([bx, cy, bx+btn_w2, cy+btn_h2], radius=48, fill=GOLD_BTN)
    draw.rounded_rectangle([bx+2, cy+2, bx+btn_w2-2, cy+btn_h2//2], radius=46, fill=(246,212,108))
    f_cta  = _font(36, bold=True)
    cta    = "무료로 내 사주 확인하기"
    ctaw   = _tw(draw, cta, f_cta)
    draw.text((CX - ctaw//2, cy + (btn_h2-36)//2), cta, font=f_cta, fill=(28,14,3))
    cy += btn_h2 + 34

    f_url = _font(26)
    url   = "moonsauj.it.com"
    uw    = _tw(draw, url, f_url)
    draw.text((CX - uw // 2, cy), url, font=f_url, fill=(155, 135, 100))

    OUTPUT_DIR.mkdir(exist_ok=True)
    path = str(OUTPUT_DIR / f"post_{post_idx:03d}_{card_num:02d}_closing.jpg")
    img.save(path, "JPEG", quality=95)
    return path


# ── 메인: 카드셋 생성 ─────────────────────────────────────
def create_card_set(content: dict, post_idx: int) -> list:
    OUTPUT_DIR.mkdir(exist_ok=True)
    paths = []

    slides = content.get("slides", [])
    if not slides:
        raise ValueError("content에 slides가 없습니다")

    title = content.get("display_title", "")
    print(f"[image_maker] 카드뉴스 제작: {title}")

    gem_prompt = _title_to_image_prompt(title)
    base       = gem_prompt or content.get("image_prompt", "")
    img_prompt = (
        f"{base}, warm rose gold tones, elegant mystical, high quality, no text no people"
        if base else
        "mystical saju fortune cosmos warm rose gold, ethereal cinematic, no text no people"
    )
    topic_img = _fal_image(img_prompt, AI_W, AI_H)

    paths.append(make_title_card(content, topic_img, post_idx))
    print("[image_maker] 1장 완료 (제목)")

    slide_list    = slides[:4]
    total_content = len(slide_list) + 1
    for i, text in enumerate(slide_list):
        paths.append(make_content_card(text, i, total_content, post_idx))
        print(f"[image_maker] {i+2}장 완료 (본문 {i+1})")

    vote_idx = len(slide_list)
    paths.append(make_vote_card(content, vote_idx, post_idx))
    print(f"[image_maker] {vote_idx+2}장 완료 (참여유도)")

    closing_num = vote_idx + 3
    paths.append(make_closing_card(post_idx, closing_num))
    print(f"[image_maker] 총 {len(paths)}장 완료")

    return paths
