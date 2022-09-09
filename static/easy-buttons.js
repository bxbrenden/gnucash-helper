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

  sourceAccount.value = eb[txnType]['source']
  destAccount.value = eb[txnType]['dest']
  descripBox.value = eb[txnType]['descrip']

  dateBox.value = getTodaysDate();
  amountBox.focus()
}
