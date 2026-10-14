const galleries = document.querySelectorAll(".product-gallery");

galleries.forEach(gallery => {
    const images = gallery.querySelectorAll(".gallery-image");
    const prevButton = gallery.querySelector(".gallery-prev");
    const nextButton = gallery.querySelector(".gallery-next");

    let currentImage = 0;

    function showImage(index) {
        images.forEach(image => {
            image.classList.remove("active");
        });

        images[index].classList.add("active");
    }

    nextButton.addEventListener("click", () => {
        currentImage = (currentImage + 1) % images.length;
        showImage(currentImage);
    });

    prevButton.addEventListener("click", () => {
        currentImage = (currentImage - 1 + images.length) % images.length;
        showImage(currentImage);
    });
});