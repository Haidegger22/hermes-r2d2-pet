// «Голос R2» — речевой пузырь R2-D2 (Hermes Agent: desktop / webapp)
//
// Плагин подписывается на поток шлюза и короткими русскими фразами говорит в
// речевом пузыре питомца, чем занят агент. Только ctx.pet.say — никаких своих
// оверлеев и правок ядра.
//
// Установка: $HERMES_HOME/desktop-plugins/r2-voice/plugin.js (по умолчанию
// ~/.hermes/desktop-plugins/r2-voice/plugin.js). Перезагрузить страницу вебаппа
// или приложение — плагин читается с диска.

const LINES = {
  start: ['берусь за дело…', 'так, поехали…', 'включаюсь в работу…', 'есть задача, иду…'],
  tool: ['кручу гайки…', 'проверяю…', 'ковыряюсь в системе…', 'смотрю файлы…', 'щёлкаю командами…'],
  done: ['готово, Артём ✨', 'всё, твой ход…', 'сделала, смотри…', 'отчитываюсь: готово…'],
  error: ['упс, сломалось…', 'не вышло, разберусь…', 'тут загвоздка…'],
  idle: ['всё под контролем…', 'проверяю датчики…', 'не сплю…', 'скучаю по задачам…', 'системы в норме…']
}

const ID = 'r2-voice'
const INFO_ID = `${ID}:info`
const ERROR_ID = `${ID}:error`
const INFO_GAP_MS = 3500
const ERROR_GAP_MS = 1500 // ошибка — самая нужная реплика, её не глушим общим окном

const pick = list => list[Math.floor(Math.random() * list.length)]

export default {
  id: ID,
  name: 'Голос R2',
  description: 'R2-D2 бормочет по-русски в речевом пузыре о том, чем занят агент',
  defaultEnabled: true,

  register(ctx) {
    const say = ctx.pet?.say?.bind(ctx.pet)

    if (!say) {
      return // старый хост без пет-двери
    }

    // Хост печатает имя плагина над каждой репликой. Прячем только СВОЙ пузырь:
    // селектор привязан к data-pet-plugin="r2-voice", чужие плагины не задеты.
    const style = document.createElement('style')

    style.textContent =
      `[data-pet-plugin="${ID}"] > span:first-child{display:none!important}` +
      `[data-pet-plugin="${ID}"]{gap:0!important;padding:5px 8px!important}` +
      // Хост зеркалит спрайт (scaleX(-1)), когда центр питомца уходит на левую
      // половину окна — это для артов, нарисованных «смотрящими влево». Наш
      // анфас смотрит на зрителя, ему переворот не нужен: гасим transform у
      // обёртки ИМЕННО нашего спрайта (по aria-label канваса). !important
      // перебивает инлайновый transform, который ставит хост.
      `div:has(> canvas[aria-label$=" pet"]){transform:none!important}`
    document.head.appendChild(style)
    ctx.onDispose(() => style.remove())

    // Раздельные окна троттлинга, чтобы «упс, сломалось» не терялось из-за
    // «кручу гайки…» за секунду до него.
    let lastInfoAt = 0
    let lastErrorAt = 0

    const speak = (text, { tone = 'info', ttlMs = 8000 } = {}) => {
      const now = Date.now()
      const isError = tone === 'error'

      if (now - (isError ? lastErrorAt : lastInfoAt) < (isError ? ERROR_GAP_MS : INFO_GAP_MS)) {
        return
      }

      if (isError) {
        lastErrorAt = now
      } else {
        lastInfoAt = now
      }

      say(text, { id: isError ? ERROR_ID : INFO_ID, tone, ttlMs })
    }

    ctx.onEvent('message.start', () => speak(pick(LINES.start)))
    ctx.onEvent('tool.start', () => speak(pick(LINES.tool)))
    // Один источник «готово» — turn.settled. message.complete дублировал бы его
    // и на длинных ходах съедал слот троттлинга.
    ctx.onEvent('turn.settled', () => speak(pick(LINES.done)))
    ctx.onEvent('message.error', () => speak(pick(LINES.error), { tone: 'error', ttlMs: 10000 }))

    // Тихая болтовня, когда долго ничего не происходит.
    ctx.setInterval(() => {
      if (Date.now() - Math.max(lastInfoAt, lastErrorAt) > 60_000) {
        speak(pick(LINES.idle), { ttlMs: 7000 })
      }
    }, 90_000)

    // Приветствие при загрузке — заодно проверка, что пузырь живой.
    ctx.setTimeout(() => {
      lastInfoAt = 0
      speak('на связи, Артём ✨', { ttlMs: 6000 })
    }, 2500)
  }
}
