import sqlite3
from datetime import datetime
from config import DATABASE 
import os
import cv2
import numpy as np
from math import sqrt, ceil, floor

if not os.path.exists("hidden_img"):
    os.mkdir("hidden_img")

class DatabaseManager:
    def __init__(self, database):
        self.database = database

    def create_tables(self):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                user_name TEXT
            )
        ''')

            conn.execute('''
            CREATE TABLE IF NOT EXISTS prizes (
                prize_id INTEGER PRIMARY KEY,
                image TEXT,
                used INTEGER DEFAULT 0
            )
        ''')

            conn.execute('''
            CREATE TABLE IF NOT EXISTS winners (
                user_id INTEGER,
                prize_id INTEGER,
                win_time TEXT,
                FOREIGN KEY(user_id) REFERENCES users(user_id),
                FOREIGN KEY(prize_id) REFERENCES prizes(prize_id)
            )
        ''')

            conn.commit()

    def add_user(self, user_id, user_name):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('INSERT INTO users VALUES (?, ?)', (user_id, user_name))
            conn.commit()

    def add_prize(self, data):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.executemany('''INSERT INTO prizes (image) VALUES (?)''', data)
            conn.commit()

    def add_winner(self, user_id, prize_id):
        win_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor() 
            cur.execute("SELECT * FROM winners WHERE user_id = ? AND prize_id = ?", (user_id, prize_id))
            if cur.fetchall():
                return 0
            else:
                conn.execute('''INSERT INTO winners (user_id, prize_id, win_time) VALUES (?, ?, ?)''', (user_id, prize_id, win_time))
                conn.commit()
                return 1

  
    def mark_prize_used(self, prize_id):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('''UPDATE prizes SET used = 1 WHERE prize_id = ?''', (prize_id,))
            conn.commit()


    def get_users(self):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor() 
            cur.execute("SELECT * FROM users")
            return [x[0] for x in cur.fetchall()] 
        
    def get_prize_img(self, prize_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor() 
            cur.execute("SELECT image FROM prizes WHERE prize_id = ?", (prize_id,))
        return cur.fetchall()[0][0]

    def get_random_prize(self):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor() 
            cur.execute("SELECT * FROM prizes WHERE used = 0 ORDER BY RANDOM()")
        return cur.fetchall()[0]
    
    def get_winners_count(self, prize_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute('SELECT COUNT(*) FROM winners WHERE prize_id = ?', (prize_id, ))
            return cur.fetchall()[0][0]
#Digunakan tanda tanya, karena id prize nya (prize_id) nya berbeda beda

    def get_rating(self):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute('''
    SELECT user_name, COUNT(*) as total FROM users 
                        INNER JOIN winners ON users.user_id = winners.user_id 
                        GROUP BY users.user_id 
                        ORDER BY total DESC
                        LIMIT 10
        ''')
            return cur.fetchall()
# Tanda * itu menghitung semua baris   

    def get_winners_img(self, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute(''' 
SELECT image FROM winners 
INNER JOIN prizes ON 
winners.prize_id = prizes.prize_id
WHERE user_id = ?''', (user_id, ))
            return cur.fetchall()
    def get_user_score(self, user_id):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM winners WHERE user_id = ?", 
            (user_id,)
        )
            return cur.fetchall()[0][0]
  
def hide_img(img_name):
    image = cv2.imread(f'img/{img_name}')
    if image is None:
        print("Gagal baca untuk hide:", img_name)
        return
    blurred_image = cv2.GaussianBlur(image, (15, 15), 0)
    pixelated_image = cv2.resize(blurred_image, (30, 30), interpolation=cv2.INTER_NEAREST)
    pixelated_image = cv2.resize(pixelated_image, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_NEAREST)
    cv2.imwrite(f'hidden_img/{img_name}', pixelated_image)

def create_collage(image_paths):
    images = []

    # Baca semua gambar
    for path in image_paths:
        image = cv2.imread(path)

        # Kalau gagal baca → skip
        if image is None:
            print("Gagal baca:", path)
            continue

        images.append(image)

    # Kalau tidak ada gambar sama sekali
    if len(images) == 0:
        print("Tidak ada gambar yang bisa dibuat kolase.")
        return None

    # Samakan ukuran ke ukuran gambar pertama
    h, w = images[0].shape[:2]
    images = [cv2.resize(img, (w, h)) for img in images]

    num_images = len(images)
    num_cols = max(1, int(sqrt(num_images)))
    num_rows = ceil(num_images / num_cols)

    # Buat kanvas kolase
    collage = np.zeros((num_rows * h, num_cols * w, 3), dtype=np.uint8)

    # Tempatkan gambar
    for i, img in enumerate(images):
        r = i // num_cols
        c = i % num_cols
        collage[r*h:(r+1)*h, c*w:(c+1)*w] = img

    return collage

m = DatabaseManager(DATABASE)
info = m.get_winners_img("user_id")
prizes = [x[0] for x in info]
for img in os.listdir("img"):
    hide_img(img)
image_paths = os.listdir('img')
image_paths = [f'img/{x}' if x in prizes else f'hidden_img/{x}' for x in image_paths]
collage = create_collage(image_paths)

if collage is not None:
    cv2.imshow('Collage', collage)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == '__main__':
    manager = DatabaseManager(DATABASE)
    manager.create_tables()
    prizes_img = os.listdir('img')
    data = [(x,) for x in prizes_img]
    manager.add_prize(data)
