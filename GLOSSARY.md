# Chathams

Chathams is a staff shop that runs on an honour system. Staff write down what they buy on a printed sheet, and the app turns those sheets into balances that staff pay off themselves.

## People

**Staff**:
A person who buys from Chathams and owes money for it. Staff sign in to see their own balance.
_Avoid_: User, customer, member

**Admin**:
A person who runs Chathams: prints sheets, uploads scans, reviews them, and manages staff.
_Avoid_: Manager, operator

## Sheets

**Ledger sheet**:
A printed template page where staff record their purchases: one row per staff member and ten price boxes per row. It has no identity of its own until it is scanned.
_Avoid_: Form, page, tab sheet

**Price box**:
One box on a ledger sheet that holds one handwritten amount.
_Avoid_: Cell, slot

**Blank row**:
A ledger sheet row with no printed staff member, where a person writes their sid by hand. Staff use it when they are not on the sheet or when their own row is full. A whole ledger sheet of blank rows is a **blank sheet**.
_Avoid_: Overflow row, spare row

**Scan**:
An uploaded PDF of filled ledger sheets. A scan gets its identity when it is uploaded.
_Avoid_: Upload, image, sheet ID

**Review**:
The step where an admin confirms or corrects the amounts read from a scan before they change any balance.
_Avoid_: Approval, verification

## Money

**Purchase**:
One amount that a staff member wrote in one price box. It can cover several items bought at the same time.
_Avoid_: Item, entry, transaction

**Balance**:
The amount a staff member owes Chathams: their purchases minus their payments.
_Avoid_: Debt, tab, account

**Payment**:
Money (cash or bank transfer) a staff member pays to reduce their balance. An admin records it, or confirms a payment claim.
_Avoid_: Deposit, settlement

**Payment claim**:
A statement by a staff member that they paid, which changes nothing until an admin confirms it.
_Avoid_: Payment request, pending payment

**Reminder**:
An email to a staff member whose balance is above the limit an admin sets.
_Avoid_: Notice, warning, dunning

## Products

**Product**:
A thing Chathams sells, with its current price.
_Avoid_: Item, stock

**Price list**:
The list of products and their prices that staff use to know what to write.
_Avoid_: Menu, catalogue

## Directory

**Directory**:
The organisation's Active Directory, where the app finds staff details by search.
_Avoid_: AD, LDAP, user store

**sid**:
The staff identifier: always seven characters, letters first, and possibly one or more digits at the end.
_Avoid_: Staff number, ID
