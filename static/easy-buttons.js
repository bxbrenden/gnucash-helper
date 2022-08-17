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

function easyFoodTransaction() {
  sourceAccount = document.getElementById('debit');
  //sourceAccount.value = "Assets:Current Assets:Cash in Wallet";
  sourceAccount.value = easyButtons.foodDebit;

  destAccount = document.getElementById('credit');
  destAccount.value = "Expenses:Dining";

  dateBox = document.getElementById('date');
  dateBox.value = getTodaysDate();

  descripBox = document.getElementById('description');
  descripBox.value = "Quick food purchase 🍕";

  amountBox = document.getElementById('amount');
  amountBox.focus()
}

window.addEventListener('load', (event) => {
  const foodButton = document.getElementById('easy-btn-food');
  foodButton.addEventListener("click", easyFoodTransaction, false);
})
