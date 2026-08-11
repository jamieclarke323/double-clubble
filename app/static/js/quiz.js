(function () {
  const quizId = window.QUIZ_ID;
  const opponent = window.QUIZ_OPPONENT;
  const totalPlayers = window.QUIZ_TOTAL;
  const siteName = window.SITE_NAME;
  const siteUrl = window.SITE_URL;

  const guessForm = document.getElementById("guess-form");
  const guessInput = document.getElementById("guess-input");
  const feedback = document.getElementById("feedback-message");
  const grid = document.getElementById("players-grid");
  const solvedCountEl = document.getElementById("solved-count");

  const shareBar = document.getElementById("share-bar");
  const shareResultBtn = document.getElementById("share-result-btn");
  const shareModalOverlay = document.getElementById("share-modal-overlay");
  const shareModalClose = document.getElementById("share-modal-close");
  const sharePreviewImage = document.getElementById("share-preview-image");
  const shareDownloadLink = document.getElementById("share-download-link");

  const clueOverlay = document.getElementById("clue-modal-overlay");
  const openClueBtn = document.getElementById("open-clue-modal");
  const clueCancelBtn = document.getElementById("clue-cancel");
  const clueSubmitBtn = document.getElementById("clue-submit");

  const giveupOverlay = document.getElementById("giveup-modal-overlay");
  const openGiveupBtn = document.getElementById("open-giveup-modal");
  const giveupCancelBtn = document.getElementById("giveup-cancel");
  const giveupConfirmBtn = document.getElementById("giveup-confirm");

  const resetOverlay = document.getElementById("reset-modal-overlay");
  const openResetBtn = document.getElementById("open-reset-modal");
  const resetCancelBtn = document.getElementById("reset-cancel");
  const resetConfirmBtn = document.getElementById("reset-confirm");

  function setFeedback(kind, message) {
    feedback.textContent = message;
    feedback.className = kind || "";
  }

  function disableAllControls() {
    guessInput.disabled = true;
    guessForm.querySelector("button").disabled = true;
    openClueBtn.disabled = true;
    openGiveupBtn.disabled = true;
  }

  function slotFor(index) {
    return grid.querySelector('.player-slot[data-index="' + index + '"]');
  }

  function fillSlot(slotEl, player) {
    slotEl.classList.add("found");
    slotEl.innerHTML =
      '<span class="slot-index">#' + (player.index + 1) + '</span>' +
      '<span class="slot-name">' + escapeHtml(player.name) + '</span>' +
      '<span class="slot-detail">' + escapeHtml(player.position || "") + '</span>' +
      '<span class="slot-detail">Charlton: ' + escapeHtml(String(player.years_charlton)) +
        ' (' + escapeHtml(String(player.apps_charlton)) + ' apps, ' +
        escapeHtml(String(player.goals_charlton)) + ' goals)</span>' +
      '<span class="slot-detail">' + escapeHtml(opponent) + ': ' + escapeHtml(String(player.years_opponent)) +
        ' (' + escapeHtml(String(player.apps_opponent)) + ' apps, ' +
        escapeHtml(String(player.goals_opponent)) + ' goals)</span>';
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  function showCongrats() {
    if (document.getElementById("congrats-banner") || document.getElementById("reveal-banner")) return;
    const banner = document.createElement("div");
    banner.className = "congrats-banner";
    banner.id = "congrats-banner";
    banner.textContent = "Congratulations! You found every Double Clubble player!";
    guessForm.parentElement.insertBefore(banner, shareBar);
    shareBar.classList.add("visible");
  }

  function showRevealBanner() {
    if (document.getElementById("congrats-banner") || document.getElementById("reveal-banner")) return;
    const banner = document.createElement("div");
    banner.className = "congrats-banner";
    banner.id = "reveal-banner";
    banner.textContent = "All answers have been revealed below.";
    guessForm.parentElement.insertBefore(banner, shareBar);
    shareBar.classList.add("visible");
  }

  guessForm.addEventListener("submit", async function (e) {
    e.preventDefault();
    const guess = guessInput.value.trim();
    if (!guess) return;

    const res = await fetch("/quiz/" + quizId + "/guess", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ guess: guess }),
    });
    const data = await res.json();

    if (data.status === "correct" || data.status === "close") {
      setFeedback(data.status, data.message);
      const slotEl = slotFor(data.player.index);
      if (slotEl) fillSlot(slotEl, data.player);
      solvedCountEl.textContent = data.solved_count;
      guessInput.value = "";
      if (data.completed) {
        disableAllControls();
        showCongrats();
      }
    } else if (data.status === "already_complete") {
      setFeedback("wrong", data.message);
    } else if (data.status === "locked") {
      setFeedback("wrong", data.message);
      disableAllControls();
    } else {
      setFeedback("wrong", data.message || "Not a match - keep trying!");
    }
  });

  // Clue modal
  openClueBtn.addEventListener("click", () => clueOverlay.classList.add("open"));
  clueCancelBtn.addEventListener("click", () => clueOverlay.classList.remove("open"));
  clueOverlay.addEventListener("click", (e) => {
    if (e.target === clueOverlay) clueOverlay.classList.remove("open");
  });

  clueSubmitBtn.addEventListener("click", async function () {
    const checked = Array.from(
      clueOverlay.querySelectorAll('input[name="clue-type"]:checked')
    ).map((cb) => cb.value);

    if (checked.length === 0) {
      return;
    }

    const res = await fetch("/quiz/" + quizId + "/clue", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ types: checked }),
    });
    const data = await res.json();
    clueOverlay.classList.remove("open");

    if (data.status !== "ok") return;

    data.clues.forEach((entry) => {
      const slotEl = slotFor(entry.index);
      if (!slotEl) return;
      const clueHolder = slotEl.querySelector("[data-clue-holder]");
      if (!clueHolder) return;
      const parts = [];
      if (entry.apps) parts.push("Apps - " + entry.apps);
      if (entry.years) parts.push("Years - " + entry.years);
      if (entry.goals) parts.push("Goals - " + entry.goals);
      if (entry.position) parts.push("Position - " + entry.position);
      if (entry.initials) parts.push("Initials - " + entry.initials);
      clueHolder.innerHTML = parts.map(escapeHtml).join("<br>");
    });
  });

  // Give up modal
  openGiveupBtn.addEventListener("click", () => giveupOverlay.classList.add("open"));
  giveupCancelBtn.addEventListener("click", () => giveupOverlay.classList.remove("open"));
  giveupOverlay.addEventListener("click", (e) => {
    if (e.target === giveupOverlay) giveupOverlay.classList.remove("open");
  });

  giveupConfirmBtn.addEventListener("click", async function () {
    const res = await fetch("/quiz/" + quizId + "/giveup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ confirm: true }),
    });
    const data = await res.json();
    giveupOverlay.classList.remove("open");

    if (data.status !== "given_up") return;

    data.players.forEach((player) => {
      const slotEl = slotFor(player.index);
      if (slotEl && !slotEl.classList.contains("found")) {
        fillSlot(slotEl, player);
      }
    });
    solvedCountEl.textContent = String(data.total);
    disableAllControls();
    showRevealBanner();
  });

  // Reset modal
  openResetBtn.addEventListener("click", () => resetOverlay.classList.add("open"));
  resetCancelBtn.addEventListener("click", () => resetOverlay.classList.remove("open"));
  resetOverlay.addEventListener("click", (e) => {
    if (e.target === resetOverlay) resetOverlay.classList.remove("open");
  });

  resetConfirmBtn.addEventListener("click", async function () {
    const res = await fetch("/quiz/" + quizId + "/reset", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ confirm: true }),
    });
    const data = await res.json();
    resetOverlay.classList.remove("open");

    if (data.status !== "reset") return;

    window.location.reload();
  });

  // Share result image
  const swordIcon = new Image();
  swordIcon.src = window.SWORD_ICON_URL;

  function buildShareCanvas(solvedCount) {
    const size = 1080;
    const canvas = document.createElement("canvas");
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext("2d");

    const gradient = ctx.createLinearGradient(0, 0, size, size);
    gradient.addColorStop(0, "#d0021b");
    gradient.addColorStop(1, "#101010");
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, size, size);

    ctx.textAlign = "center";

    if (swordIcon.complete && swordIcon.naturalWidth > 0) {
      const iconH = 170;
      const iconW = (swordIcon.naturalWidth / swordIcon.naturalHeight) * iconH;
      ctx.drawImage(swordIcon, (size - iconW) / 2, 100, iconW, iconH);
    }

    ctx.fillStyle = "#ffffff";
    ctx.font = "700 76px 'Century Gothic', 'Trebuchet MS', sans-serif";
    ctx.fillText(siteName.toUpperCase(), size / 2, 370);

    ctx.font = "700 34px 'Trebuchet MS', sans-serif";
    ctx.fillStyle = "#f2d9dd";
    ctx.fillText((opponent + " vs Charlton Athletic").toUpperCase(), size / 2, 430);

    ctx.font = "700 220px 'Century Gothic', 'Trebuchet MS', sans-serif";
    ctx.fillStyle = "#ffffff";
    ctx.fillText(solvedCount + " / " + totalPlayers, size / 2, 680);

    ctx.font = "700 30px 'Trebuchet MS', sans-serif";
    ctx.fillStyle = "#f2d9dd";
    ctx.fillText("DOUBLE CLUBBLE PLAYERS FOUND", size / 2, 740);

    ctx.strokeStyle = "rgba(255,255,255,0.5)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(size / 2 - 120, 900);
    ctx.lineTo(size / 2 + 120, 900);
    ctx.stroke();

    ctx.font = "700 30px 'Trebuchet MS', sans-serif";
    ctx.fillStyle = "#ffffff";
    ctx.fillText(siteUrl, size / 2, 960);

    return canvas;
  }

  function showShareFallback(blob) {
    const url = URL.createObjectURL(blob);
    sharePreviewImage.src = url;
    shareDownloadLink.href = url;
    shareModalOverlay.classList.add("open");
  }

  shareResultBtn.addEventListener("click", async function () {
    const solvedCount = Number(solvedCountEl.textContent);
    const canvas = buildShareCanvas(solvedCount);

    canvas.toBlob(async function (blob) {
      if (!blob) return;
      const file = new File([blob], "double-clubble-result.png", { type: "image/png" });
      const shareData = {
        files: [file],
        title: siteName,
        text: "I found " + solvedCount + "/" + totalPlayers + " Double Clubble players for " + opponent + " vs Charlton Athletic!",
      };

      if (navigator.canShare && navigator.canShare({ files: [file] })) {
        try {
          await navigator.share(shareData);
          return;
        } catch (err) {
          // Fall through to the fallback preview if sharing was cancelled/unsupported.
        }
      }
      showShareFallback(blob);
    }, "image/png");
  });

  shareModalClose.addEventListener("click", () => shareModalOverlay.classList.remove("open"));
  shareModalOverlay.addEventListener("click", (e) => {
    if (e.target === shareModalOverlay) shareModalOverlay.classList.remove("open");
  });
})();
