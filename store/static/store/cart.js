document.querySelectorAll(".cart-control").forEach(control => {
    const form = control.querySelector(".cart-add-form");
    const counter = control.querySelector(".quantity-control");
    const input = control.querySelector(".quantity-input");
    const minusButton = control.querySelector(".quantity-minus");
    const plusButton = control.querySelector(".quantity-plus");

    const url = control.dataset.url;
    const csrfToken = form.querySelector(
        '[name="csrfmiddlewaretoken"]'
    ).value;

    const stock = Number(control.dataset.stock);
    let currentQuantity = Number(control.dataset.quantity);

    function renderQuantity() {
        form.hidden = currentQuantity > 0;
        counter.hidden = currentQuantity === 0;

        input.value = currentQuantity;
        minusButton.disabled = currentQuantity <= 0;
        plusButton.disabled = currentQuantity >= stock;
    }

    async function updateCart(action, quantity = null) {
        const body = new URLSearchParams({ action });

        if (quantity !== null) {
            body.set("quantity", String(quantity));
        }

        try {
            const response = await fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-CSRFToken": csrfToken
                },
                body: body.toString(),
                credentials: "same-origin"
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Cart update failed");
            }

            currentQuantity = data.quantity;
            control.dataset.quantity = String(currentQuantity);

            renderQuantity();

        } catch (error) {
            input.value = currentQuantity;
            console.error("Cart update failed:", error);
        }
    }

    form.addEventListener("submit", event => {
        event.preventDefault();
        updateCart("add");
    });

    plusButton.addEventListener("click", () => {
        updateCart("increase");
    });

    minusButton.addEventListener("click", () => {
        updateCart("decrease");
    });

    input.addEventListener("change", () => {
        const value = input.value.trim();
        const quantity = Number(value);

        if (
            value === "" ||
            !Number.isInteger(quantity)
        ) {
            input.value = currentQuantity;
            return;
        }

        updateCart("set", quantity);
    });

    renderQuantity();

    window.addEventListener("pageshow", function (event) {
    if (event.persisted) {
        window.location.reload();
    }
    });
});