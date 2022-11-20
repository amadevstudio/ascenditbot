from urllib.parse import unquote


def message_master(
		bot, chat_id, text, markup=None, message_id=None,
		imgMode=False, photoUrl=None, resending=False, postloading=False,
		pmode="Markdown", disable_web_page_preview=False):
	# resending: позволяет принудительно отправить сообщение повторно
	# message_id: id сообщения, которое необходимо заменить, но если
	# 	сейчас картинка, то id картинки для удаления
	# postloading: хоть сейчас и изображение, но оно уже было изменено на
	# 	"загрузка...", поэтому необходима обработка как у текстового
	try:
		# https%3A%2F%2F -> https://
		if photoUrl is not None and isinstance(photoUrl, str):
			photoUrl = unquote(photoUrl)

		if resending or storage.get_user_resend_flag(chat_id):
			if imgMode is False:
				answer = bot.send_message(
					chat_id, text, parse_mode=pmode, reply_markup=markup,
					disable_web_page_preview=disable_web_page_preview)
			else:
				answer = bot.send_message(
					chat_id, text, parse_mode=pmode,
					disable_web_page_preview=disable_web_page_preview)
				try:
					bot.send_photo(chat_id=chat_id, photo=photoUrl, reply_markup=markup)
				except Exception as e:
					print("mainf/message_master_resendin_photo: ", e, flush=True)
					bot.send_photo(chat_id=chat_id, photo=noPhoto, reply_markup=markup)

			storage.del_user_resend_flag(chat_id)
			storage.set_user_last_text(chat_id, answer.message_id)
			return answer

		else:
			if imgMode is False:
				try:
					# если то, что вызвало, есть текстовое сообщение
					if storage.get_user_curr_state(chat_id) in textMessages or postloading:
						bot.edit_message_text(
							chat_id=chat_id, message_id=message_id, text=text,
							parse_mode=pmode, reply_markup=markup,
							disable_web_page_preview=disable_web_page_preview)

					# если сейчас картинка, то правим последнее текстовое и удаляем картинку
					elif storage.get_user_curr_state(chat_id) in imgMessages:
						bot.edit_message_text(
							chat_id=chat_id, message_id=storage.get_user_last_text(chat_id),
							text=text, parse_mode=pmode, reply_markup=markup,
							disable_web_page_preview=disable_web_page_preview)
						bot.delete_message(chat_id=chat_id, message_id=message_id)

					# иначе просто отправляем новое сообщение
					else:
						answer = bot.send_message(
							chat_id, text, parse_mode=pmode, reply_markup=markup,
							disable_web_page_preview=disable_web_page_preview)
						storage.del_user_resend_flag(chat_id)
						storage.set_user_last_text(chat_id, answer.message_id)
				except Exception:
					answer = bot.send_message(
						chat_id, text, parse_mode=pmode, reply_markup=markup,
						disable_web_page_preview=disable_web_page_preview)
					storage.del_user_resend_flag(chat_id)
					storage.set_user_last_text(chat_id, answer.message_id)
			else:
				try:
					# если то, что вызвало, есть текстовое сообщение
					if storage.get_user_curr_state(chat_id) in textMessages or postloading:
						bot.edit_message_text(
							chat_id=chat_id, message_id=message_id,
							text=text, parse_mode=pmode,
							disable_web_page_preview=disable_web_page_preview)
						try:
							bot.send_photo(chat_id=chat_id, photo=photoUrl, reply_markup=markup)
						except Exception:
							bot.send_photo(chat_id=chat_id, photo=noPhoto, reply_markup=markup)

					# если сейчас картинка
					elif storage.get_user_curr_state(chat_id) in imgMessages:
						bot.edit_message_text(
							chat_id=chat_id, message_id=storage.get_user_last_text(chat_id),
							text=text, parse_mode=pmode,
							disable_web_page_preview=disable_web_page_preview)
						photo = types.InputMedia(type="photo", media=photoUrl)
						bot.edit_message_media(
							chat_id=chat_id, message_id=message_id,
							media=photo, reply_markup=markup)

					# иначе просто отправляем новое сообщение
					else:
						answer = bot.send_message(
							chat_id, text, parse_mode=pmode,
							disable_web_page_preview=disable_web_page_preview)
						try:
							bot.send_photo(chat_id=chat_id, photo=photoUrl, reply_markup=markup)
						except Exception:
							bot.send_photo(chat_id=chat_id, photo=noPhoto, reply_markup=markup)
						storage.del_user_resend_flag(chat_id)
						storage.set_user_last_text(chat_id, answer.message_id)
				except Exception:
					answer = bot.send_message(chat_id, text, parse_mode=pmode)
					try:
						bot.send_photo(chat_id=chat_id, photo=photoUrl, reply_markup=markup)
					except Exception:
						bot.send_photo(chat_id=chat_id, photo=noPhoto, reply_markup=markup)
					storage.del_user_resend_flag(chat_id)
					storage.set_user_last_text(chat_id, answer.message_id)
	except Exception as e:
		timeout = get_timeout_from_error_bot(e)
		if timeout:
			time.sleep(timeout)
			message_master(
				bot, chat_id, text, markup, message_id,
				imgMode, photoUrl, resending, postloading,
				pmode, disable_web_page_preview)
			return

		print(f"\n\nError! Can't send message! {e}\n\n")
		bot_blocked_reaction(e, chat_id)