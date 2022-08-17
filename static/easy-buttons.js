function getTodaysDate() {
  let today = new Date();
  let dd = String(today.getDate()).padStart(2, '0');
  let mm = String(today.getMonth() + 1).padStart(2, '0'); //January is 0!
  let yyyy = today.getFullYear();
  let dateString = yyyy + "-" + mm + "-" + dd

  return dateString
}

function getEasyButtons(buttons) {
  // This is a hack
  // see here: https://stackoverflow.com/questions/37259740/passing-variables-from-flask-to-javascript
  return buttons
}

function easyTransaction(evt) {
  let txnType = evt.currentTarget.txnType;
  let sourceAccount = document.getElementById('debit');
  let destAccount = document.getElementById('credit');
  let dateBox = document.getElementById('date');
  let descripBox = document.getElementById('description');
  let amountBox = document.getElementById('amount');

  let eb = easyButtons;

  if (txnType === 'food') {
    sourceAccount.value = eb['food']['source'];
    destAccount.value = eb['food']['dest'];
    descripBox.value = eb['food']['descrip'];
  } else if (txnType === 'fun') {
    sourceAccount.value = eb['fun']['source'];
    destAccount.value = eb['fun']['dest'];
    descripBox.value = eb['fun']['descrip'];
  } else if (txnType === 'cats') {
    sourceAccount.value = eb['cats']['source'];
    destAccount.value = eb['cats']['dest'];
    descripBox.value = eb['cats']['descrip'];
  } else if (txnType === 'misc') {
    sourceAccount.value = eb['misc']['source'];
    destAccount.value = eb['misc']['dest'];
    descripBox.value = eb['misc']['descrip'];
  }

  dateBox.value = getTodaysDate();
  amountBox.focus()
}

window.addEventListener('load', (event) => {
  const foodButton = document.getElementById('easy-btn-food');
  foodButton.addEventListener("click", easyTransaction, false);
  foodButton.txnType = 'food'

  const funButton = document.getElementById('easy-btn-fun');
  funButton.addEventListener("click", easyTransaction, false);
  funButton.txnType = 'fun'

  const catsButton = document.getElementById('easy-btn-cats');
  catsButton.addEventListener("click", easyTransaction, false);
  catsButton.txnType = 'cats'

  const miscButton = document.getElementById('easy-btn-misc');
  miscButton.addEventListener("click", easyTransaction, false);
  miscButton.txnType = 'misc'
})
