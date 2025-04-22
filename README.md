# SP2025: Group &lt;11&gt; &lt;Receiptablity&gt;

Name your repository using the following format:  
**SP2025_Group_&lt;Group Number&gt;**  
(Example: SP2025_Group_9)

## Team Members
- **&lt;Member Name&gt;**: &lt;e.keskin@wustl.edu&gt; ; &lt;EgeKeskin&gt;
- **&lt;Member Name&gt;**: &lt;n.stuart@wustl.edu&gt; ; &lt;nicoStuart&gt;
- **&lt;Member Name&gt;**: &lt;h.sawyer@wustl.edu&gt; ; &lt;shelzberg1&gt;

## TA
&lt;Mutaz&gt;

## Objectives
&lt;Receiptability is a full service web application that enables users to scan and itemize receipts. The app then allows users to join "Tables" where they can split and itemize each receipt. Underlying the app, there is a software that gamifies the splitting of the receipt, enabling the users to take risks on payment in exchange to potential pay more or less than their order. Our app uses OCR and AI technology to scan each receipt. Django is the primary tech stak our group utilized.&gt;

## How to Run
&lt;Instructions for how to run your project. Include the URI to your project at the top if applicable.&gt;
https://receiptablity2.onrender.com/


## Website Instructions (also found on the site)
How to Use Our Site:
Follow these steps to get started:

Login or Register
If you already have an account, click on the Login button at the top right corner and enter your credentials. If you don’t have an account, click on Register and fill out the sign-up form. You must be logged in to create a room.

Create a Room & Upload a Receipt
Once you’re logged in, click on the Make Room option to create a new room. Here, you can upload an image of your receipt. Our system will process the receipt and display its details in a unique "receipt room" page.

Select a Pricing Strategy
Price Roulette: This option will randomly assign the full value of the total meal to one person (so no one else will need to pay). Spin the wheel and pray it’s not you!

Probabilistic Price Roulette: This option will allow each person to individually control their odds of winning and their willingness to pay (how much are you willing to risk?). Each person’s odds of winning are multiplied by each person’s willingness to pay to form their expected value (we have designated this the effective weight), which you can see and change when you move each slider. By default, the effective weight is set to an even split (i.e., if the total meal value is $120, it will be automatically initially set to $40 per person). Dial this up to your liking!

Pay For Your Own Stuff: This option enables each person to look through the items and choose which ones they paid for so everyone can individually pay for their own items.

Split Evenly: This option simply divides the total meal value by the number of people in the group or room to provide an even split so everyone pays the same amount.

I’m Feeling Lucky: Can’t decide which pricing strategy to select? I’m Feeling Lucky will choose one at random for you!

Share the Receipt Link
After your receipt is processed, copy the URL from your browser’s address bar and share it with anyone who needs to view the receipt details. They can visit that link to see the receipt information without logging in.

Pay! (Or maybe not…)
