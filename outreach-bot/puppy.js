const puppeteer = require('puppeteer');
const fs = require('fs');


const axios = require('axios');

async function sendPostRequest(user_input, url) {
  try {
    const response = await axios.post('http://localhost:5000/reddit_response', {
      input: user_input,
      url: url
    });

    console.log(response.data); // Assuming the response is JSON data
    return response.data.response
  } catch (error) {
    console.error('Error:', error);
  }
}

function pickRandomElement(array) {
  const randomIndex = Math.floor(Math.random() * array.length);
  return array[randomIndex];
}


(async () => {
  // Replace 'your_username' and 'your_password' with your actual Reddit credentials

  const username = process.env.REDDIT_USERNAME;
  const password = process.env.REDDIT_PASSWORD;

  subreddits = [
    'Spanish',
    'Spanishhelp',
    'learnspanish',
    'languagelearning',
    'languagelearningjerk',
    'LearnSpanishInReddit',
    'duolingo',
    'language',
    'language_exchange',
    'Language_Exchange',
    'LanguageExchange',
    'LanguageTechnology',
    'LanguageBuds',
    'LatinLanguage',
    'LearnANewLanguage',
    'German',
    'Russian',
    'translator',
    'HindiLanguage',
    'French',
    'FrenchMemes',
    'learnfrench',
    'FrenchImmersion',
    'easy_french'
  ]

  const browser = await puppeteer.launch({
    headless: false,
    args: ['--disable-notifications'] // Disable notifications
  }); // Launch browser
  let page = await browser.newPage(); // Create a new page

  await page.setViewport({ width: 1200, height: 800 });


  page = await loginToReddit(page, username, password, 'Spanish');

  for (let i=0; i<90; i++) {

    let subreddit = pickRandomElement(subreddits)
    let success = await makeAComment(page, subreddit);
    if (success) {
      let sleepTimeSecondsMin = 60
      let sleepTimeSecondsMax = 240
      const randomSleepTime = Math.floor(Math.random() * (sleepTimeSecondsMax - sleepTimeSecondsMin)) + sleepTimeSecondsMin;
  
      await new Promise(resolve => setTimeout(resolve, randomSleepTime*1000));
    }

  }

  browser.close()
})();

function uniqueStrings(array) {
  return [...new Set(array)];
}

async function loginToReddit(page, username, password, subreddit) {

  // await page.setUserAgent('Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0');

  try {
    // Navigate to Reddit login page
    await page.goto('https://www.reddit.com/login/?dest=https%3A%2F%2Fwww.reddit.com%2Fsettings%2F', { waitUntil: 'networkidle0' });

    // Fill in the username and password fields
    await page.type('input[name="username"]', username);
    await page.type('input[name="password"]', password);

    // Press the Enter key after typing the password
    await page.keyboard.press('Enter');

    // Wait for navigation after pressing Enter
    await page.waitForNavigation({ waitUntil: 'networkidle0' });


    // Check if login was successful
    if (page.url().startsWith('https://www.reddit.com')) {
      console.log('Login successful!');
    } else {
      console.log('Login failed. Please check your credentials.');
    }
    return page
  } catch (error) {
    console.log('unable to log in!')
    return
  }
}

async function makeAComment(page, subreddit) {
  try {
    // Navigate to the 'spanish' subreddit
    let retryCount = 0;
    // let subreddit = 'Spanish'
    // let threadIndex = 2;

    let activeUrl = ''
    while (retryCount < 3) { // Retry up to 3 times
      try {
        await page.goto(`https://www.reddit.com/r/${subreddit}/`, { waitUntil: 'networkidle0' });

        const aTags = await page.$$eval('a', anchors => anchors.map(anchor => anchor.outerHTML));
        // console.log(aTags)
        const linksArray = aTags.map(html => {
          const match = html.match(/href="([^"]*)"/);
          return match ? match[1] : null;
        }).filter(link => link !== null)
          .filter(link => link.includes(`/${subreddit}/`))
          .filter(link => link.includes('/comments/'));

        let uniqueThreads = uniqueStrings(linksArray)

        const prefixedUrls = uniqueThreads.map(url => {
          if (!url.startsWith('https://www.reddit.com')) {
            return 'https://www.reddit.com' + url;
          }
          return url;
        });

        console.log(prefixedUrls);

        function pickRandomThread(urls) {
          const startIndex = 3; // Number of URLs to ignore
          const randomIndex = Math.floor(Math.random() * (urls.length - startIndex)) + startIndex;
          return urls[randomIndex];
        }

        let randomThreadUrl = pickRandomThread(prefixedUrls)
        activeUrl = randomThreadUrl
        // Click on the nth post in the subreddit
        await Promise.all([
          page.goto(randomThreadUrl),
          page.waitForNavigation({ waitUntil: 'networkidle0' })
        ]);

        break;
      } catch (error) {
        console.log('some error', error)
        console.log('retrying...', retryCount)
        retryCount += 1;
      }
    }


    // step two pull some information about the post and generate a comment that makes sense
    const text = await page.evaluate(() => {
      const h1Element = document.querySelector('h1');
      return h1Element ? h1Element.textContent.trim() : null;
    });
    console.log('h1', text)

    // post content from the p tags
    const postText = await page.evaluate(() => {
      const pTags = Array.from(document.querySelectorAll('p')).slice(0, 5);
      return pTags.map(p => p.textContent.trim());
    });


    // step three make the comment
    const replyButtons = await page.waitForSelector('button ::-p-text(Reply)');
    console.log(replyButtons)

    const commentContainer = await page.evaluate(replyButtons => {
      return replyButtons.parentElement.parentElement.parentElement.textContent.trim();
    }, replyButtons);

    console.log(commentContainer)

    gpt_input = `community: ${subreddit} title ${text} post text ${postText} reply to this comment ${commentContainer}`
    let gpt_comment = await sendPostRequest(gpt_input, activeUrl)
    console.log('gpt comment', gpt_comment)


    // // Click on the first comment to respond

    // Write and submit a response
    const textContainer = await page.waitForSelector('.public-DraftEditor-content')
    console.log('container', textContainer)

    const textInput5 = await page.waitForSelector('.public-DraftEditor-content div div div div span')
    console.log('container4', textInput5)

    await replyButtons.click()

    await new Promise(resolve => setTimeout(resolve, 10*1000));


    await textInput5.type(gpt_comment)

    await page.keyboard.press('Tab');
    await page.keyboard.press('Enter');

    await new Promise(resolve => setTimeout(resolve, 5000));

    console.log('Response submitted successfully!');
    return true;

  } catch (error) {
    console.error('An error occurred:', error);
    return false;
  }
}
