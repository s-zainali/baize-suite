import { onMounted, onUnmounted } from 'vue'

const DEFAULT_BACKGROUND = ''

/**
 * Paint the document background for as long as this page is mounted.
 *
 * Pages used to do this by hand with onMounted/onUnmounted, which broke on
 * every RouterLink navigation: Vue mounts the incoming component BEFORE
 * unmounting the outgoing one, so the old page's cleanup wiped the colour the
 * new page had just set. A reload looked fine because nothing unmounted.
 *
 * Clearing only when the current value is still ours makes the order
 * irrelevant — a page that has already been superseded leaves well alone.
 */
export function usePageBackground(color) {
    const apply = () => {
        document.documentElement.style.backgroundColor = color
        document.body.style.backgroundColor = color
    }

    const release = () => {
        if (document.body.style.backgroundColor !== color) return
        document.documentElement.style.backgroundColor = DEFAULT_BACKGROUND
        document.body.style.backgroundColor = DEFAULT_BACKGROUND
    }

    onMounted(apply)
    onUnmounted(release)

    return { apply, release }
}