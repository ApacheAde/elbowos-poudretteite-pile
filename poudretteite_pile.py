#!/usr/bin/env python3
"""Poudretteite Pile — neon slab-stack arcade for ElbowOS. Python 3 + pygame.

A timing stacker: a glowing slab rides a rail. Drop it onto the tower.
Overhang shears away. Perfect seats bloom. Not a tetromino well.
"""
import math
import os
import random
import subprocess
import sys

RECORD = "--record" in sys.argv or os.environ.get("ELBOWOS_RECORD") == "1"
PLAY = "--play" in sys.argv
if RECORD or not PLAY:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get(
    "ELBOWOS_MP4", "/workspace/artifacts/POUDRETTEITE_PILE_ElbowOS.mp4"
)
TITLE, HANDLE = "POUDRETTEITE PILE", "x.com/ElbowOS"
INK = (22, 6, 18)
ROSE = (236, 120, 168)
CORAL = (255, 154, 92)
GOLD = (255, 214, 120)
AQUA = (92, 232, 210)
CREAM = (255, 236, 228)
HUES = (ROSE, CORAL, GOLD, AQUA)


class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        flags = 0 if PLAY else pygame.HIDDEN
        try:
            self.screen = pygame.display.set_mode((W, H), flags)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.display.quit()
            pygame.display.init()
            self.screen = pygame.display.set_mode((W, H), pygame.HIDDEN)
        pygame.display.set_caption(TITLE)
        self.canvas = pygame.Surface((W, H))
        self.font = pygame.font.SysFont("dejavusans", 64, bold=True)
        self.small = pygame.font.SysFont("dejavusans", 36, bold=True)
        self.tiny = pygame.font.SysFont("dejavusans", 28, bold=True)
        self.reset()

    def reset(self):
        self.t = 0
        self.score = 0
        self.combo = 0
        self.lives = 3
        self.flash = 0
        self.banner = ""
        self.banner_t = 0
        self.sparks = []
        self.motes = [
            [random.randrange(W), random.randrange(H), random.uniform(0.4, 1.6)]
            for _ in range(48)
        ]
        self.stack = [{"x": W / 2, "y": 1500, "w": 460, "h": 52, "c": ROSE}]
        self.spawn_mover()

    def spawn_mover(self):
        top = self.stack[-1]
        self.mw = max(120, top["w"])
        self.mx = 140 + self.mw / 2
        self.dir = 1 if random.random() < 0.5 else -1
        self.speed = 9 + min(14, len(self.stack) * 0.55)
        self.hue = HUES[len(self.stack) % len(HUES)]
        self.drop_cd = 0

    def burst(self, x, y, col, n=18):
        for _ in range(n):
            a = random.random() * math.tau
            s = random.uniform(2, 9)
            self.sparks.append([x, y, math.cos(a) * s, math.sin(a) * s, col, 18])

    def drop(self):
        top = self.stack[-1]
        left = max(self.mx - self.mw / 2, top["x"] - top["w"] / 2)
        right = min(self.mx + self.mw / 2, top["x"] + top["w"] / 2)
        overlap = right - left
        if overlap < 36:
            self.lives -= 1
            self.combo = 0
            self.banner, self.banner_t = "SHEAR", 28
            self.burst(self.mx, top["y"] - 20, CORAL, 26)
            self.flash = 10
            if self.lives <= 0:
                self.reset()
                self.banner, self.banner_t = "RESTACK", 32
                return
            self.spawn_mover()
            return
        nx = (left + right) / 2
        perfect = abs(self.mx - top["x"]) < 14
        gain = 50 + self.combo * 10 + (40 if perfect else 0)
        self.score += gain
        self.combo = self.combo + 1 if perfect else 0
        ny = top["y"] - 52
        self.stack.append({"x": nx, "y": ny, "w": overlap, "h": 52, "c": self.hue})
        self.banner = "BLOOM" if perfect else "SET"
        self.banner_t = 18
        self.burst(nx, ny + 20, GOLD if perfect else self.hue, 24 if perfect else 12)
        self.flash = 8 if perfect else 3
        if len(self.stack) > 16:
            self.stack.pop(0)
        self.spawn_mover()

    def auto(self):
        top = self.stack[-1]
        aligned = abs(self.mx - top["x"]) < 10
        self.drop_cd += 1
        if aligned and self.drop_cd > 8:
            self.drop()
        elif self.drop_cd > 46:
            self.drop()

    def update(self, keys, tap):
        self.t += 1
        self.mx += self.dir * self.speed
        half = self.mw / 2
        if self.mx - half < 70:
            self.mx = 70 + half
            self.dir = 1
        if self.mx + half > W - 70:
            self.mx = W - 70 - half
            self.dir = -1
        if PLAY and tap:
            self.drop()
        elif not PLAY:
            self.auto()
        for m in self.motes:
            m[1] -= m[2]
            if m[1] < 0:
                m[1] = H
                m[0] = random.randrange(W)
        alive = []
        for s in self.sparks:
            s[0] += s[2]
            s[1] += s[3]
            s[5] -= 1
            if s[5] > 0:
                alive.append(s)
        self.sparks = alive
        if self.flash:
            self.flash -= 1
        if self.banner_t:
            self.banner_t -= 1

    def draw_slab(self, s, y, glow=False):
        x = int(s["x"] - s["w"] / 2)
        w = int(s["w"])
        r = pygame.Rect(x, int(y), w, int(s["h"]))
        col = s["c"]
        if glow:
            pygame.draw.rect(self.canvas, col, r.inflate(16, 10), border_radius=14)
        pygame.draw.rect(self.canvas, col, r, border_radius=12)
        inner = r.inflate(-18, -16)
        if inner.w > 8:
            pygame.draw.rect(self.canvas, CREAM, inner, border_radius=8)
        pygame.draw.rect(self.canvas, (40, 8, 24), r, 3, border_radius=12)

    def draw(self):
        c = self.canvas
        c.fill(INK)
        for i in range(8):
            shade = (48 + i * 6, 12, 36 + i * 4)
            pygame.draw.rect(c, shade, (0, i * 240, W, 240))
        for m in self.motes:
            pygame.draw.circle(c, (255, 180, 210), (int(m[0]), int(m[1])), 3)
        # rail
        pygame.draw.line(c, (90, 30, 60), (60, 280), (W - 60, 280), 6)
        pygame.draw.circle(c, GOLD, (60, 280), 10)
        pygame.draw.circle(c, GOLD, (W - 60, 280), 10)
        # tower base plinth
        base = self.stack[0]
        cam = 0
        top_y = self.stack[-1]["y"]
        if top_y < 620:
            cam = 620 - top_y
        for s in self.stack:
            self.draw_slab(s, s["y"] + cam)
        mover = {"x": self.mx, "w": self.mw, "h": 52, "c": self.hue}
        self.draw_slab(mover, 228, glow=True)
        # fulcrum gem under stack
        bx = int(base["x"])
        by = int(base["y"] + 52 + cam)
        pygame.draw.polygon(
            c, (120, 40, 70), [(bx - 80, by + 70), (bx + 80, by + 70), (bx, by)]
        )
        if self.flash:
            veil = pygame.Surface((W, H), pygame.SRCALPHA)
            veil.fill((255, 200, 220, 40 + self.flash * 6))
            c.blit(veil, (0, 0))
        for s in self.sparks:
            pygame.draw.circle(c, s[4], (int(s[0]), int(s[1] + cam * 0.2)), max(2, s[5] // 4))
        title = self.font.render(TITLE, True, CREAM)
        c.blit(title, (W // 2 - title.get_width() // 2, 70))
        score = self.small.render(f"SCORE  {self.score}", True, GOLD)
        c.blit(score, (70, 160))
        lives = self.small.render("LIVES  " + "◆" * self.lives, True, ROSE)
        c.blit(lives, (W - lives.get_width() - 70, 160))
        handle = self.tiny.render(HANDLE, True, AQUA)
        c.blit(handle, (W // 2 - handle.get_width() // 2, H - 80))
        if self.banner_t:
            b = self.font.render(self.banner, True, GOLD)
            c.blit(b, (W // 2 - b.get_width() // 2, 860))
        hint = self.tiny.render("SPACE drop   A/D wait on the rail", True, (210, 160, 180))
        c.blit(hint, (W // 2 - hint.get_width() // 2, H - 140))
        self.screen.blit(c, (0, 0))
        pygame.display.flip()

    def record(self):
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        cmd = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
            "-movflags", "+faststart", OUT,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        frames = FPS * SECS
        try:
            for _ in range(frames):
                self.update({}, False)
                self.draw()
                proc.stdin.write(pygame.image.tostring(self.canvas, "RGB"))
            proc.stdin.close()
            err = proc.stderr.read().decode("utf-8", "replace")
            code = proc.wait(timeout=60)
        except Exception:
            proc.kill()
            raise
        if code != 0:
            raise SystemExit(f"ffmpeg failed ({code})\n{err[-1500:]}")
        print(OUT)

    def play(self):
        clock = pygame.time.Clock()
        while True:
            tap = False
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return
                if e.type == pygame.KEYDOWN and e.key in (pygame.K_SPACE, pygame.K_RETURN):
                    tap = True
                if e.type == pygame.KEYDOWN and e.key == pygame.K_r:
                    self.reset()
            self.update(pygame.key.get_pressed(), tap)
            self.draw()
            clock.tick(FPS)


if __name__ == "__main__":
    g = Game()
    if PLAY:
        g.play()
    else:
        g.record()
