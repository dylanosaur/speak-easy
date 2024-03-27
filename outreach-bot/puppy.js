const puppeteer = require('puppeteer');
const fs = require('fs');
const axios = require('axios');

(async () => {

  const username_1 = process.env.REDDIT_USERNAME_1;
  const password_1 = process.env.REDDIT_PASSWORD_1;

  const username_2 = process.env.REDDIT_USERNAME_2;
  const password_2 = process.env.REDDIT_PASSWORD_2;

  const username_3 = process.env.REDDIT_USERNAME_3;
  const password_3 = process.env.REDDIT_PASSWORD_3;

  const username_4 = process.env.REDDIT_USERNAME_4;
  const password_4 = process.env.REDDIT_PASSWORD_4;


  let usersConfig = require('./users.json')
  let users = usersConfig.data
  console.log(users)


  subreddits = ['announcements', 'Fauxmoi', 'language', 'language_exchange',
    'ChineseLanguage', 'languagelearning', 'linguistics', 'LanguageExchange',
    'Language_Exchange', 'LanguageTechnology', 'duolingo', 'languagelearningjerk',
    'LanguageBuds', 'LatinLanguage', 'conlangs', 'AskReddit', 'AskReddit',
    'Japaneselanguage', 'LearnANewLanguage', 'MapPorn', 'programming', 'latin',
    'ThaiLanguage', 'Showerthoughts', 'todayilearned', 'Korean', 'C_Programming',
    'LearnJapanese', 'LearnJapanese', 'AskEurope', 'EnglishLearning',
    'learnprogramming', 'ProgrammingLanguages', 'signlanguage', 'golang',
    'asklinguistics', 'ProgrammerHumor', 'Assembly_language', 'rust',
    'NoStupidQuestions', 'memes', 'c_language', 'turkish', 'AskHistorians',
    'programmingcirclejerk', 'd_language', 'PhyrexianLanguage', 'teenagers',
    'teenagers', 'German', 'German', 'swift', 'learnspanish', 'europe', 'russian',
    'Tagalog', 'badlinguistics', 'translator', 'translator', 'PolishLanguagePodcast',
    'HindiLanguage', 'linguisticshumor', 'india', 'slp', 'NaturalLanguage', 'WritingPrompts',
    'explainlikeimfive', 'TatarLanguage', 'languagexchange', 'unpopularopinion',
    'worldbuilding', 'Rlanguage', 'dartlang', 'politics', 'Politics', 'shittysuperpowers',
    'shittysuperpowers', 'programming_language', 'GothicLanguage', 'GothicLanguage',
    'funny', 'polls', 'Language_Resources', 'languagelearning', 'dankmemes', 'videos',
    'ChozoLanguage', 'bodylanguage', 'MachineLearning', 'AskBalkans', 'GachaLanguage',
    'gachaedits', 'BodyLanguageAnalysis', 'science', 'worldnews', 'LanguageComics',
    'HelloTalk', 'GCSE', 'GCSE', 'haskell', 'CornishLanguage', 'LanguagePals',
    'softwaregore', 'ireland', 'italian_language', 'SpanishLanguage', 'LightLanguage',
    'LanguageSwap', 'germany', 'english_language', 'SergalLanguage', 'EncapsulatedLanguage',
    'LanguageTransfer', 'language_lesson', 'malayalam_language', 'NeapolitanLanguage',
    'CarbonLanguage', 'circassian_language', 'KoreanLanguage', 'LanguageBuddies',
    'LanguageNerds', 'HTML', 'LanguageMugs', 'PitbullbodyLanguage', 'Learn_Language',
    'hebrew', 'Hebrew', 'walloon_language', 'DropsLanguage', 'LanguageAdventure',
    'ClarityLanguage', 'marathi_language', 'language_tutoring', 'czech_language',
    'MojoLanguage', 'NepaliLanguage']

  let attempts = 0
  while (attempts < 100) {
    attempts += 1

    let user = pickRandomElement(users)
    let username = user.username
    let password = user.password
    console.log('switching to new proxy', user)
    await updateProxy(user)

    const browserHandle = await setupBrowser();
    const browser = browserHandle.browser
    const page = browserHandle.page

    try {

      let loginFailed = await loginToReddit(page, username, password);
      if (loginFailed) {
        console.log('bad proxy or credentials, continuing')
        browser.close()
        continue;
      }

      await generateComments(page, subreddits, 20)
      browser.close()
    } catch (error) {
      console.log('global error oops', error)
      browser.close()
    }
  }

})();

async function updateProxy(user) {
  let username = user.username;
  let password = user.password;
  let vpnConfig = user.vpnConfig;

  // Function to delete a file if it exists
  const deleteIfExists = (filePath) => {
    if (fs.existsSync(filePath)) {
      fs.unlinkSync(filePath);
    }
  };

  // Delete existing update.txt and vpnStable.lock files if they exist
  deleteIfExists('/home/dylan/proxies/tcp/update.txt');
  deleteIfExists('/home/dylan/proxies/tcp/vpnStable.lock');

  // Create update.txt file and write vpnConfig to it
  fs.writeFileSync('/home/dylan/proxies/tcp/update.txt', vpnConfig);

  // Function to wait until a file exists
  const waitForFile = (filePath) => {
    return new Promise((resolve) => {
      const checkFile = () => {
        if (fs.existsSync(filePath)) {
          resolve();
        } else {
          setTimeout(checkFile, 5000); // Check every second
        }
      };
      checkFile();
    });
  };

  // Wait until vpnStable.lock file exists and then delete it
  await waitForFile('/home/dylan/proxies/tcp/vpnStable.lock');
  deleteIfExists('/home/dylan/proxies/tcp/vpnStable.lock');

  // Sleep for 5 seconds
  await new Promise(resolve => setTimeout(resolve, 5000));
};

const writeJSONToFile = (filePath, data) => {
  try {
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
    console.log(`JSON data has been written to ${filePath}`);
  } catch (error) {
    console.error(`Error writing JSON data to ${filePath}: ${error}`);
  }
};

function readJSONFile(filepath, callback) {
  fs.readFile(filepath, 'utf8', (err, data) => {
    if (err) {
      callback(err, null);
      return;
    }
    try {
      const jsonData = JSON.parse(data);
      callback(null, jsonData);
    } catch (error) {
      callback(error, null);
    }
  });
}

async function setupBrowser() {

  const browser = await puppeteer.launch({
    headless: false,
    timeout: 60000,
    args: [
      '--disable-notifications',
    ]
  }); // Launch browser
  const page = await browser.newPage(); // Create a new page

  await page.setViewport({ width: 1200, height: 800 });

  // // Set up request interception handler
  // const proxyIndex = Math.floor(Math.random() * 8 + 1);

  // writeJSONToFile('session.json', { 'session-id': `session_${proxyIndex}` })
  // console.log('using proxy', proxyIndex)
  // await new Promise(resolve => setTimeout(resolve, 300 * 1000));

  // await page.goto('https://www.google.com')

  return { browser, page }
}

async function checkIPBlock(page) {
  try {

    const textContent = await page.evaluate(() => {
      return document.body.textContent;
    });
    console.log(textContent)
    if (textContent.includes("This site can't be reached")) {
      return true
    } else if (textContent.includes("blocked")) {
      return true
    }
  } catch (error) {
    console.log('cant determine if ip is blocked')
  }
}

function pickRandomElement(array) {
  const randomIndex = Math.floor(Math.random() * array.length);
  return array[randomIndex];
}

const generateComments = async (page, subreddits, nComments) => {
  let commentsMade = 0
  while (commentsMade < nComments) {

    commentsMade += 1

    let subreddit = pickRandomElement(subreddits)

    threadFound = await navigateToThread(page, subreddit)
    if (!threadFound) {
      console.log("unable to find thread on subreddit", subreddit)
      continue
    }

    let success = await makeAComment(page, subreddit);
    if (success) {
      // let sleepTimeSecondsMin = 100
      // let sleepTimeSecondsMax = 300
      // const randomSleepTime = Math.floor(Math.random() * (sleepTimeSecondsMax - sleepTimeSecondsMin)) + sleepTimeSecondsMin;
      // await new Promise(resolve => setTimeout(resolve, randomSleepTime * 1000));
      console.log('comment was made!')
    } else {
      let pageUrl = await page.url()
      console.log("unable to comment on thread", pageUrl)
    }

  }
}

function uniqueStrings(array) {
  return [...new Set(array)];
}



async function acceptCookies(page) {

  // return true for failed login
  try {
    // Navigate to Reddit login page
    await page.goto('https://www.reddit.com/', { waitUntil: 'networkidle0', timeout: 300000 });

    const firstButton = await page.$('button');
    firstButton.click()
    console.log('button clicked')
  } catch (error) {
    console.log(error)
  }
}

async function loginToReddit(page, username, password) {

  // return true for failed login
  try {
    // Navigate to Reddit login page
    await page.goto('https://www.reddit.com/login/?dest=https%3A%2F%2Fwww.reddit.com%2Fsettings%2F', { waitUntil: 'networkidle0', timeout: 300000 });

    await new Promise(resolve => setTimeout(resolve, 10 * 1000));

    // Fill in the username and password fields
    await page.type('input[name="username"]', username);
    await page.type('input[name="password"]', password);

    // Press the Enter key after typing the password
    await page.keyboard.press('Enter');

    // Wait for navigation after pressing Enter
    await page.waitForNavigation({ waitUntil: 'networkidle0', timeout: 300000 });

    // Check if login was successful
    if (page.url().startsWith('https://www.reddit.com')) {
      console.log('Login successful!');
      return
    } else {
      console.log('Login failed. Please check your credentials.');
      return true
    }
    return false
  } catch (error) {
    console.log('unable to log in?', error)
    // return false
    return true
  }
}

async function navigateToThread(page, subreddit) {
  try {
    let retryCount = 0;
    while (retryCount < 3) { // Retry up to 3 times
      try {
        await page.goto(`https://www.reddit.com/r/${subreddit}`, { waitUntil: 'networkidle0', timeout: 300000 });

        await new Promise(resolve => setTimeout(resolve, 2 * 1000));

        await page.evaluate(() => {
          window.scrollBy(0, window.innerHeight); // Scroll down by the height of the viewport
        });

        await new Promise(resolve => setTimeout(resolve, 1 * 1000));

        const aTags = await page.$$eval('a', anchors => anchors.map(anchor => anchor.outerHTML));
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
        // Click on the nth post in the subreddit
        await Promise.all([
          page.goto(randomThreadUrl),
          page.waitForNavigation({ waitUntil: 'networkidle0', timeout: 300000 })
        ]);

        return true;
      } catch (error) {
        console.log('some error', error)
        console.log('retrying...', retryCount)
        retryCount += 1;
      }
      return true;
    }
  } catch (error) {
    console.log("some errorr navigating to thread", error)
  }
}


async function getGPTComment(user_input, url) {
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

async function markUrlAsSuccess(url) {
  try {
    const response = await axios.post('http://localhost:5000/reddit_response_success', {
      url: url
    });

    console.log(response.data); // Assuming the response is JSON data
    return response
  } catch (error) {
    console.error('Error:', error);
  }
}


async function makeAComment(page, subreddit) {

  try {
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

    // let refReplyButton = await page.$eval('button ::-p-text(Reply)', bu);
    // console.log('reply button', refReplyButton)
    let refReplyButtons = await page.$$eval('button ::-p-text(Reply)', buttons => buttons);
    console.log('reply buttons', refReplyButtons)
    let randomIndex = 0
    if (refReplyButtons) {
      let numberReplyButtons = refReplyButtons.length;
      if (numberReplyButtons == 0) {
        return false;
      }
      randomIndex = Math.floor(Math.random() * Math.min(numberReplyButtons, 3));
    }

    let replyButtons = await page.$$('button ::-p-text(Reply)');
    let randomReplyButton = replyButtons[randomIndex]

    const commentContainer = await page.evaluate(randomReplyButton => {
      return randomReplyButton.parentElement.parentElement.parentElement.parentElement.parentElement.textContent.trim().replace(/\n/g, '');
    }, randomReplyButton);

    gpt_input = `community: ${subreddit} title ${text} post text ${postText} reply to this comment ${commentContainer}`
    let currentUrl = await page.url()
    let gpt_comment = await getGPTComment(gpt_input, currentUrl)
    console.log('gpt comment', gpt_comment)
    if (!gpt_comment) {
      return false;
    }

    await new Promise(resolve => setTimeout(resolve, 10 * 1000));

    await randomReplyButton.click()
    await new Promise(resolve => setTimeout(resolve, 10 * 1000));
    await page.keyboard.type(gpt_comment)
    await page.keyboard.press('Tab');
    await page.keyboard.press('Enter');
    await new Promise(resolve => setTimeout(resolve, 5000));
    console.log('Response submitted successfully!');
    await markUrlAsSuccess(currentUrl)
    return true;

  } catch (error) {
    console.error('An error occurred:', error);
    return false;
  }
}

