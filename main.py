import glob
import random
import discord
import io
import asyncio
import sqlite3
import os
from dotenv import load_dotenv
from PIL import Image

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
        msg = 'Bảng Xếp Hạng Server hiện tại\n'
        sql = 'SELECT user_id, coin FROM tbl_users WHERE guild_id=? ORDER BY coin DESC'
        sv_id = int(message.channel.guild.id)
        cursor.execute(sql, (sv_id, ))
        rows = cursor.fetchall()
        for index, row in enumerate(rows):
            user = await bot.fetch_user(row[0])
            msg += f'{index+1}. {user.name}: {row[1]*1000:,}đ\n'
        await message.channel.send(msg)
        cursor.close()
        con.close()
        return

    if content == 'reg':
        con = sqlite3.connect('db.sqlite')
        cursor = con.cursor()
        server_id = int(message.channel.guild.id)
        x = cursor.execute("""
            INSERT OR IGNORE INTO tbl_users(user_id, guild_id) VALUES (?, ?)
        """, (message.author.id, server_id))
        n = x.rowcount
        con.commit()
        cursor.close()
        con.close()
        if n > 0:
            await message.channel.send(f'Tài khoản {message.author.name} đã đăng ký thành công vào mã server {server_id}. Nhận 100.000đ làm vốn')
        else:
            await message.channel.send('Đã đăng ký tài khoản!')
        return

    if content == 'chk':
        con = sqlite3.connect('db.sqlite')
        cursor = con.cursor();
        cursor.execute("""
            SELECT coin FROM tbl_users WHERE user_id LIKE ? AND guild_id=?
        """, (message.author.id, int(message.channel.guild.id)))
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
        predict_msg = await message.channel.send('Đặt nào bà con. 10k/cửa, vui lòng đặt trước khi súc sắc biến mất!')
        for emo in emoji:
            await predict_msg.add_reaction(emo)
        # Send dice gif
        message = await message.channel.send(file=discord.File('dice.gif'))

        # Generate
        result = random.choices([i for i in range(len(images))], k=3)
        imgs = [Image.open(images[i]) for i in result]
        width, height = imgs[0].size
        total_width = width*len(imgs)
        new_im = Image.new('RGB', (total_width, height))
        offset = 0
        for img in imgs:
            new_im.paste(img, (offset, 0))
            offset += width
        correct_cell = tuple(emoji[i] for i in result)
        await asyncio.sleep(10)
        msg = await message.channel.fetch_message(message.id)
        await msg.delete()
        after = await message.channel.fetch_message(predict_msg.id)
        result = {}
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
        
        with io.BytesIO() as buffer:
            new_im.save(buffer, 'PNG')
            buffer.seek(0)
            await message.channel.send(file=discord.File(fp=buffer, filename='fuckyou.png'))

        c = 'Kết quả:\n'
        con = sqlite3.connect('db.sqlite')
        cursor = con.cursor()
        data = []
        for i, u in result.items():
            tien = f'{abs(u*10_000):,} đ'
            if u > 0:
                c += f'{i.name}: ăn {tien}\n'
            elif u < 0:
                c += f'{i.name}: thua {tien}\n'
            else:
                c += f'{i.name}: huề vốn\n'
            data.append((u*10, i.id, int(message.channel.guild.id)))
        cursor.executemany("""
            UPDATE tbl_users SET coin = coin + ? WHERE user_id LIKE ? AND guild_id=?
        """, data)
        con.commit()
        cursor.close()
        con.close()
        await message.channel.send(c)

load_dotenv()
bot.run(os.getenv('TOKEN'))