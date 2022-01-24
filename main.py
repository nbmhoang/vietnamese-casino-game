TOKEN = ''

import glob
import random
import discord
import cv2
from time import sleep
import sqlite3

bot = discord.Client()

images = sorted(glob.glob('images/*.png'))
emoji = ('<:XXNai:934083405631590550>', '<:XXBau:934083430361227274>', '<:XXGa:934081793097887844>',
            '<:XXCa:934083439643213855>', '<:XXCua:934083448275083304>', '<:XXTom:934083420345221180>', )
last_msg = ''

@bot.event
async def on_ready():
    print("We have logged in as {0.user}".format(bot))

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.lower()

    if content == 'top':
        con = sqlite3.connect('db.sqlite')
        cursor = con.cursor()        
        msg = 'Bảng Xếp Hạng - Top 5 players nhiều tiền nhất\n'
        sql = 'SELECT user_id, coin FROM tbl_users ORDER BY coin DESC LIMIT 5'
        cursor.execute(sql)
        rows = cursor.fetchall()
        for index, row in enumerate(rows):
            user = await bot.fetch_user(row[0])
            msg += f'{index+1}. {user.name}: {row[1]:,}đ\n'
        await message.channel.send(msg)
        cursor.close()
        con.close()
        return

    if content == 'reg':
        con = sqlite3.connect('db.sqlite')
        cursor = con.cursor()
        x = cursor.execute("""
            INSERT OR IGNORE INTO tbl_users(user_id) VALUES (?)
        """, (message.author.id, ))
        n = x.rowcount
        con.commit()
        cursor.close()
        con.close()
        if n > 0:
            await message.channel.send(f'Tài khoản {message.author.name} đã đăng ký thành công. Nhận 100.000đ làm vốn')
        else:
            await message.channel.send('Đăng ký rồi đăng ký lại làm gì nữa vậy cha')
        return

    if content == 'chk':
        con = sqlite3.connect('db.sqlite')
        cursor = con.cursor();
        cursor.execute("""
            SELECT coin FROM tbl_users WHERE user_id LIKE ?
        """, (message.author.id, ))
        rs = cursor.fetchone()
        if not rs:
            await message.channel.send('Tài khoản chưa đăng ký. Gọi reg để đăng ký và nhận tiền')
            return

        coin = rs[0]
        con.commit()
        cursor.close()
        con.close()
        await message.channel.send(f'Số dư của {message.author.name} là {coin*1000:,}đ')
        return

    if content == 'xx':
        predict_msg = await message.channel.send('Đặt nào bà con')
        for emo in emoji:
            await predict_msg.add_reaction(emo)
        # Send dice gif
        message = await message.channel.send(file=discord.File('dice.gif'))

        # Generate
        result = random.choices([i for i in range(len(images))], k=3)
        imgs = []
        for index in result:
            imgs.append(cv2.imread(images[index]))
        img_h = cv2.hconcat(imgs)
        cv2.imwrite('result.png', img_h)
        sleep(10)

        correct_cell = tuple(emoji[i] for i in result)

        msg = await message.channel.fetch_message(message.id)
        await msg.delete()
        after = await message.channel.fetch_message(predict_msg.id)
        result = {}
        s = set()
        for reaction in after.reactions:
            users = await reaction.users().flatten()
            is_correct = str(reaction.emoji) in correct_cell
            for u in users:
                user_id = u.id
                if user_id != bot.user.id:
                    c = result.get(u)
                    if c is None:
                        if is_correct:
                            result[u] = correct_cell.count(str(reaction.emoji))
                        else:
                            result[u] = -1
                    else:
                        if is_correct:
                            result[u] += correct_cell.count(str(reaction.emoji))
                        else:
                            result[u] -= 1
                
        
        await message.channel.send(file=discord.File('result.png'))
        c = 'Kết quả:\n'
        con = sqlite3.connect('db.sqlite')
        cursor = con.cursor()
        for i, u in result.items():
            tien = f'{abs(u*10_000):,} đ'
            if u > 0:
                c += f'{i.name}: ăn {tien}\n'
            elif u < 0:
                c += f'{i.name}: thua {tien}\n'
            else:
                c += f'{i.name}: huề vốn\n'
            cursor.execute("""
                UPDATE tbl_users SET coin = coin + ? WHERE user_id LIKE ?
            """, (u*10, i.id))
        con.commit()
        cursor.close()
        con.close()
        await message.channel.send(c)

bot.run(TOKEN)