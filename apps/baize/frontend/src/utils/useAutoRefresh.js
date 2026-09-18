import { onMounted, onUnmounted, onActivated, onDeactivated } from 'vue'

/**
 * Keep a view in step with the server.
 *
 * Both the staff dashboard and the customer home page fetched once on mount and
 * never again, so anything created elsewhere — a guest booking online, a
 * receptionist starting a session — only appeared after a manual refresh.
 *
 * Polling alone isn't quite enough on a tablet that sits locked behind the
 * counter: the interval keeps firing while the screen is off, and the moment
 * someone picks it up they still see data up to one interval old. So the timer
 * pauses while the tab is hidden and fires immediately on the way back.
 *
 * @param {() => any} fetcher   the refresh function (may be async)
 * @param {number}    everyMs   poll interval while the tab is visible
 */
export function useAutoRefresh(fetcher, everyMs = 10000) {
    let timer = null
    let running = false

    async function refresh() {
        // Skip if the previous request is still in flight, so a slow network
        // can't stack up overlapping calls.
        if (running || document.hidden) return
        running = true
        try {
            await fetcher()
        } finally {
            running = false
        }
    }

    function start() {
        stop()
        timer = setInterval(refresh, everyMs)
    }

    function stop() {
        if (timer) clearInterval(timer)
        timer = null
    }

    function onVisibilityChange() {
        if (document.hidden) {
            stop()
        } else {
            refresh()   // catch up straight away, then resume the cadence
            start()
        }
    }

    onMounted(() => {
        refresh()
        start()
        document.addEventListener('visibilitychange', onVisibilityChange)
        window.addEventListener('focus', refresh)
    })

    // Under <KeepAlive> a page isn't unmounted when you navigate away — it's
    // deactivated. Without these, every page you'd ever opened would keep
    // polling in the background. Pause on the way out, catch up on the way back.
    // (These hooks simply never fire for a component that isn't kept alive, so
    // this stays a no-op change for any view rendered the old way.)
    onActivated(() => {
        refresh()
        start()
    })

    onDeactivated(() => {
        stop()
    })

    onUnmounted(() => {
        stop()
        document.removeEventListener('visibilitychange', onVisibilityChange)
        window.removeEventListener('focus', refresh)
    })

    return { refresh, stop, start }
}