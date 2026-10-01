// Show a random quote at the top of the home page, picked from the #quote-pool template.
const pool = document.getElementById("quote-pool")
const cards = pool ? pool.content.querySelectorAll(".quote") : []
const section = document.querySelector(".random")
const slot = document.getElementById("random-slot")

if (section && slot && cards.length) {
    let last = -1

    const pick = () => {
        let i
        do {
            i = Math.floor(Math.random() * cards.length)
        } while (cards.length > 1 && i === last)
        last = i

        const card = cards[i].cloneNode(true)
        card.removeAttribute("id")
        slot.replaceChildren(card)
    }

    document.getElementById("shuffle").addEventListener("click", pick)
    pick()
    section.hidden = false
}
