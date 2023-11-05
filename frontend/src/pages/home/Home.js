import React, { useState } from 'react';
import axios, { all } from 'axios';
import './home.css'
import { Line } from 'react-chartjs-2';
import 'chart.js/auto';

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
  const [combinedData, setCombinedData] = useState({
    labels: [],
    datasets: []
  });

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
        const quarterToArticles = getArticles();
        const sentimentSeries = performSentimentAnalysis(quarterToArticles);
        const allData = getAllData(sentimentSeries);
        generateGraph("Close", allData);

    } catch (error) {
        console.error('Error running analysis:', error);
        // Handle error appropriately
    }
}

const getArticles = async () => {
    try {
        setIsSubmitted(true);
        const response = await axios.get(`/get_articles_by_quarter?company_name=${encodeURIComponent(companyName)}`);
        console.log(response.data);
        return response.data;
        // Assuming the response.data is the array of articles
    } catch (error) {
        console.error('Error fetching articles:', error);
        // Handle error appropriately
    }
};

const performSentimentAnalysis = async (quarterToArticles) => {
    try {
        const sentimentResponse = await axios.post('/sentiment_analysis', {
            "quarter_to_articles": quarterToArticles
        });
        console.log(sentimentResponse.data);
        return sentimentResponse.data;
    } catch (error) {
      console.error('Error fetching articles:', error);
      // Handle error appropriately
    }
  };

    const getAllData = async (sentiments) => {
        try {
            const predictionResponse = await axios.post('/predictions', {
                "company_name": companyName,
                "sentiments": sentiments
            });
            return predictionResponse.data;
        } catch (error) {
        console.error('Error fetching articles:', error);
        // Handle error appropriately
        }
    };

    const generateGraph = async (metric, allData) => {
        try {
            const data = getData(metric, allData);
            const predictions = getPredictions(metric, allData);
            console.log(data['x_vals']);
            console.log(predictions['x_vals']);
            const allQuarters = data["x_vals"].concat(predictions["x_vals"]);
            const dataFromDataFrame1 = {
                datasets: [
                  {
                    label: data['y_label'],
                    data: data['vals'], // This should be your actual data
                    borderColor: 'rgb(255, 99, 132)', // Color for Dataset 1
                    backgroundColor: 'rgba(255, 99, 132, 0.5)',
                  },
                ],
              };
              
            const dataFromDataFrame2 = {
            datasets: [
                {
                label: predictions['y_label'],
                data: predictions['vals'], // This should be your actual data
                borderColor: 'rgb(54, 162, 235)', // Color for Dataset 2
                backgroundColor: 'rgba(54, 162, 235, 0.5)',
                },
            ],
            };
            setCombinedData({
                labels: allQuarters, // make sure allQuarters is an array of labels
                datasets: [...dataFromDataFrame1.datasets, ...dataFromDataFrame2.datasets],
              });
        } catch (error) {
            console.error('Error fetching articles:', error);
        }
    }

    const getData= async (metric, allData) => {
        try {
            const response = await axios.post('/get_data', {
                "metric": metric,
                "all_data": allData
            });
            return response.data;
        } catch (error) {
        console.error('Error fetching articles:', error);
        // Handle error appropriately
        }
    };

    const getPredictions= async (metric, allData) => {
        try {
            const response = await axios.post('/get_predictions', {
                "metric": metric,
                "all_data": allData
            });
            return response.data;
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
        <Line data={combinedData}/>
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
