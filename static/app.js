document.addEventListener("DOMContentLoaded", () => {
  const questionForm = document.getElementById("question-form");
  const questionInput = document.getElementById("question-input");
  const questionSubmitButton = document.querySelector(".question-submit-button");
  const exampleChips = document.querySelectorAll(".example-chip");

  const setLoadingState = () => {
    if (questionSubmitButton) {
      questionSubmitButton.disabled = true;
      questionSubmitButton.classList.add("is-loading");
      questionSubmitButton.textContent = "Getting help...";
    }
  };

  const submitQuestionForm = () => {
    if (!questionForm) {
      return;
    }
    setLoadingState();
    questionForm.submit();
  };

  if (questionInput && questionForm) {
    questionInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        submitQuestionForm();
      }
    });
  }

  if (questionForm) {
    questionForm.addEventListener("submit", () => {
      setLoadingState();
    });
  }

  for (const chip of exampleChips) {
    chip.addEventListener("click", () => {
      if (questionInput) {
        questionInput.value = chip.dataset.question;
      }
      submitQuestionForm();
    });
  }

  const responseCard = document.getElementById("response");
  if (responseCard) {
    responseCard.scrollIntoView({ behavior: "auto", block: "start" });
  }
});
