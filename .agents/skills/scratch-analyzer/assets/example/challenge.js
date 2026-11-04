const quiz = document.querySelector('.quiz');
const feedback = quiz.querySelector('.feedback');
const responses = {
  510: '再看一次積木順序。510% 是進入迴圈前的尺寸，第一輪會先縮小 2 個百分點才蓋章。',
  508: '答對了。先設定 510%，第一輪先減 2，再蓋章，所以第一枚印記是 508%。',
  512: '再看一次尺寸改變的數值。原作使用 −2，所以第一輪的尺寸會從 510% 降到 508%。',
};

quiz.addEventListener('submit', event => {
  event.preventDefault();
  const choice = new FormData(quiz).get('size');
  feedback.textContent = responses[choice] || '請先選一個答案。';
});

quiz.addEventListener('reset', () => {
  feedback.textContent = '';
});
