// «Голос R2» — речевой пузырь R2-D2 (Пятница, Pi4)
//
// Плагин Desktop/Webapp: подписывается на поток шлюза и короткими русскими
// фразами говорит в речевом пузыре питомца, чем занята Пятница.
// Только ctx.pet.say — никаких своих оверлеев и правок ядра.
//
// Ставится в ~/.hermes/desktop-plugins/r2-voice/plugin.js

const LINES = {
  start: ['берусь за дело…', 'так, поехали…', 'включаюсь в работу…', 'есть задача, иду…'],
  tool: ['кручу гайки…', 'проверяю…', 'ковыряюсь в системе…', 'смотрю файлы…', 'щёлкаю командами…'],
  done: ['готово, Артём ✨', 'всё, твой ход…', 'сделала, смотри…', 'отчитываюсь: готово…'],
  error: ['упс, сломалось…', 'не вышло, разберусь…', 'тут загвоздка…'],
  idle: ['всё под контролем…', 'проверяю датчики…', 'не сплю…', 'скучаю по задачам…', 'системы в норме…']
}

const pick = list => list[Math.floor(Math.random() * list.length)]

export default {
  id: 'r2-voice',
  name: 'Голос R2',
  description: 'R2-D2 бормочет по-русски в речевом пузыре о том, чем занята Пятница',
  defaultEnabled: true,

  register(ctx) {
    const say = ctx.pet?.say?.bind(ctx.pet)

    if (!say) {
      return // старый хост без пет-двери
    }

    // Пузырь рисует надпись с именем плагина над репликой — она лишняя и
    // съедает высоту. Прячем только её, остальные пузыри не трогаем.
    const style = document.createElement('style')

    style.textContent =
      '[data-slot="pet-plugin-bubble"] > span:first-child{display:none!important}' +
      '[data-slot="pet-plugin-bubble"]{gap:0!important;padding:5px 8px!important}'
    document.head.appendChild(style)
    ctx.onDispose(() => style.remove())

    let lastSaidAt = 0

    // Не чаще одной фразы в 3.5 с: шина шлёт tool.start пачками, а лимит хоста
    // — 10 «say» за 10 с на плагин.
    const speak = (text, options = {}) => {
      const now = Date.now()

      if (now - lastSaidAt < 3500) {
        return
      }

      lastSaidAt = now
      say(text, { id: 'r2-voice', ttlMs: 8000, ...options })
    }

    ctx.onEvent('message.start', () => speak(pick(LINES.start)))
    ctx.onEvent('tool.start', () => speak(pick(LINES.tool)))
    ctx.onEvent('turn.settled', () => speak(pick(LINES.done)))
    ctx.onEvent('message.complete', () => speak(pick(LINES.done)))
    ctx.onEvent('message.error', () => speak(pick(LINES.error), { tone: 'error', ttlMs: 10000 }))

    // Тихая болтовня, когда долго ничего не происходит.
    ctx.setInterval(() => {
      if (Date.now() - lastSaidAt > 60_000) {
        speak(pick(LINES.idle), { ttlMs: 7000 })
      }
    }, 90_000)

    // Приветствие при загрузке — заодно проверка, что пузырь живой.
    ctx.setTimeout(() => {
      lastSaidAt = 0
      speak('на связи, Артём ✨', { ttlMs: 6000 })
    }, 2500)
  }
}
