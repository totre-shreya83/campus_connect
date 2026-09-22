document.addEventListener("DOMContentLoaded", function () {

    const toasts = document.querySelectorAll(".cc-toast");

    toasts.forEach(function (toast) {

        setTimeout(function () {
            toast.classList.add("cc-toast-hide");

            setTimeout(function () {
                toast.remove();
            }, 300);

        }, 4000);

    });

});
