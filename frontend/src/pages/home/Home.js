import React, { useState } from 'react';
import axios from 'axios';
import './home.css'

const companyNames = [
    'Apple',
    'Microsoft',
    'Google',
    'Amazon',
    'Meta',
    'Tesla',
    'Goldman Sachs'
  ];

function Home() {
  const [companyName, setCompanyName] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleInputChange = (event) => {
    const inputValue = event.target.value;
    setCompanyName(inputValue);
    if (inputValue.length > 0) {
        const regex = new RegExp(`^${inputValue}`, 'i');
        setSuggestions(companyNames.sort().filter(v => regex.test(v)));
      } else {
        setSuggestions([]);
      }
  };

  const onSuggestionClick = (value) => {
    setCompanyName(value);
    setSuggestions([]);
  };

const handleKeyPress = (event) => {
    // It will trigger by pressing the Enter key
    if (event.key === 'Enter') {
        runAnalysis();
    }
};

const runAnalysis = async () => {
    try {
        const quarterlyArticleLists = getArticles();
        performSentimentAnalysis(quarterlyArticleLists);
    } catch (error) {
        console.error('Error running analysis:', error);
        // Handle error appropriately
    }
}

const getArticles = async () => {
    try {
        setIsSubmitted(true);
        const response = await axios.get(`/get_articles_by_quarter?company_name=${encodeURIComponent(companyName)}`);
        return response.data;
        // Assuming the response.data is the array of articles
    } catch (error) {
        console.error('Error fetching articles:', error);
        // Handle error appropriately
    }
};

const performSentimentAnalysis = async (quarterlyArticleLists) => {
    try {
        const sentimentResponse = await axios.post('/sentiment_analysis', {
            
        });
    } catch (error) {
      console.error('Error fetching articles:', error);
      // Handle error appropriately
    }
  };


  return (
    <div className="homepage">
        <div className={`search-container ${isSubmitted ? 'at-top' : 'centered'}`}>
            <h1 className="search-heading">Input a company name below!</h1>
            <input
            type="text"
            value={companyName}
            onChange={handleInputChange}
            onKeyDown={handleKeyPress}
            placeholder="Enter company name"
            className="search-input"
            />
            {suggestions.length > 0 && (<div className="suggestions-container">
                {suggestions.map((suggestion, index) => (
                <div key={index} className="suggestion-row" onClick={() => onSuggestionClick(suggestion)}>
                    <span className ="company-name">{suggestion}</span>
                </div>
                ))}
            </div>)}
        </div>
        {/* {quarterToArticles.length > 0 && (
        <div>
            <h2>Articles</h2>
            <ul>
                {quarterToArticles.map(quarterArticles => (
                    <li>
                        {quarterArticles.map(article => (
                        <div>
                            <h3>Article from {article.publisher.title}</h3>
                            <ul>
                                <li>{article.title}</li>
                                <li><a href={article.url}>{article.url}</a></li>
                                <li>{article["published date"]}</li>
                            </ul>
                        </div>
                    ))}
                    </li>
                ))}
            </ul>
        </div>
        )} */}
    </div>
  );
}

export default Home;
