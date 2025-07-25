/**
 * Feedback Widget for collecting user corrections on SQL responses
 */
class FeedbackWidget {
    constructor(apiEndpoint) {
        this.apiEndpoint = apiEndpoint;
        this.currentMessageId = null;
        this.currentSessionId = null;
        this.userContext = null;
    }

    showFeedbackForm(messageId, sessionId, originalQuery, originalResponse, userContext) {
        this.currentMessageId = messageId;
        this.currentSessionId = sessionId;
        this.userContext = userContext;

        const feedbackHtml = `
            <div id="feedback-modal" class="feedback-modal">
                <div class="feedback-content">
                    <h3>Improve this response</h3>
                    <div class="feedback-section">
                        <label>Rate this response:</label>
                        <div class="rating-stars">
                            ${[1,2,3,4,5].map(i => `<span class="star" data-rating="${i}">★</span>`).join('')}
                        </div>
                    </div>
                    
                    <div class="feedback-section">
                        <label>What was wrong with this response?</label>
                        <select id="problem-category">
                            <option value="">Select a category</option>
                            <option value="wrong_table">Used wrong table</option>
                            <option value="syntax_error">SQL syntax error</option>
                            <option value="missing_where_clause">Missing WHERE clause</option>
                            <option value="incorrect_joins">Incorrect table joins</option>
                            <option value="wrong_columns">Wrong column names</option>
                            <option value="other">Other</option>
                        </select>
                    </div>
                    
                    <div class="feedback-section">
                        <label>Corrected SQL (optional):</label>
                        <textarea id="corrected-response" placeholder="Provide the correct SQL query...">${originalResponse}</textarea>
                    </div>
                    
                    <div class="feedback-section">
                        <label>Additional notes:</label>
                        <textarea id="feedback-notes" placeholder="Explain what was wrong and how to fix it..."></textarea>
                    </div>
                    
                    <div class="feedback-buttons">
                        <button id="submit-feedback" class="btn-primary">Submit Feedback</button>
                        <button id="cancel-feedback" class="btn-secondary">Cancel</button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', feedbackHtml);

        this.attachEventListeners(originalQuery, originalResponse);
    }

    attachEventListeners(originalQuery, originalResponse) {
        document.querySelectorAll('.star').forEach(star => {
            star.addEventListener('click', (e) => {
                const rating = parseInt(e.target.dataset.rating);
                this.setRating(rating);
            });
        });

        document.getElementById('submit-feedback').addEventListener('click', () => {
            this.submitFeedback(originalQuery, originalResponse);
        });

        document.getElementById('cancel-feedback').addEventListener('click', () => {
            this.closeFeedbackForm();
        });

        document.getElementById('feedback-modal').addEventListener('click', (e) => {
            if (e.target.id === 'feedback-modal') {
                this.closeFeedbackForm();
            }
        });
    }

    setRating(rating) {
        document.querySelectorAll('.star').forEach((star, index) => {
            star.classList.toggle('selected', index < rating);
        });
        this.selectedRating = rating;
    }

    async submitFeedback(originalQuery, originalResponse) {
        const correctedResponse = document.getElementById('corrected-response').value.trim();
        const feedbackNotes = document.getElementById('feedback-notes').value.trim();
        const problemCategory = document.getElementById('problem-category').value;

        if (!correctedResponse && !feedbackNotes && !this.selectedRating) {
            alert('Please provide a rating, correction, or feedback notes.');
            return;
        }

        const feedbackData = {
            messageId: this.currentMessageId,
            sessionId: this.currentSessionId,
            feedbackType: correctedResponse ? 'correction' : 'rating',
            rating: this.selectedRating || null,
            originalQuery: originalQuery,
            originalResponse: originalResponse,
            correctedResponse: correctedResponse || null,
            feedbackNotes: feedbackNotes || null,
            problemCategory: problemCategory || null,
            userContext: this.userContext
        };

        try {
            const response = await fetch(`${this.apiEndpoint}/feedback`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(feedbackData)
            });

            if (response.ok) {
                const result = await response.json();
                this.showSuccessMessage('Thank you for your feedback! This will help improve future responses.');
                this.closeFeedbackForm();
            } else {
                throw new Error('Failed to submit feedback');
            }
        } catch (error) {
            console.error('Error submitting feedback:', error);
            alert('Error submitting feedback. Please try again.');
        }
    }

    showSuccessMessage(message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'feedback-success';
        successDiv.textContent = message;
        document.body.appendChild(successDiv);

        setTimeout(() => {
            successDiv.remove();
        }, 3000);
    }

    closeFeedbackForm() {
        const modal = document.getElementById('feedback-modal');
        if (modal) {
            modal.remove();
        }
    }
}

const feedbackStyles = `
    .feedback-modal {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
    }
    
    .feedback-content {
        background: white;
        padding: 20px;
        border-radius: 8px;
        max-width: 500px;
        width: 90%;
        max-height: 80vh;
        overflow-y: auto;
    }
    
    .feedback-section {
        margin-bottom: 15px;
    }
    
    .feedback-section label {
        display: block;
        margin-bottom: 5px;
        font-weight: bold;
    }
    
    .rating-stars .star {
        font-size: 24px;
        color: #ddd;
        cursor: pointer;
        margin-right: 5px;
    }
    
    .rating-stars .star.selected {
        color: #ffd700;
    }
    
    .feedback-section textarea {
        width: 100%;
        min-height: 80px;
        padding: 8px;
        border: 1px solid #ddd;
        border-radius: 4px;
    }
    
    .feedback-section select {
        width: 100%;
        padding: 8px;
        border: 1px solid #ddd;
        border-radius: 4px;
    }
    
    .feedback-buttons {
        display: flex;
        gap: 10px;
        justify-content: flex-end;
        margin-top: 20px;
    }
    
    .btn-primary, .btn-secondary {
        padding: 10px 20px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    }
    
    .btn-primary {
        background: #007bff;
        color: white;
    }
    
    .btn-secondary {
        background: #6c757d;
        color: white;
    }
    
    .feedback-success {
        position: fixed;
        top: 20px;
        right: 20px;
        background: #28a745;
        color: white;
        padding: 15px;
        border-radius: 4px;
        z-index: 1001;
    }
`;

const styleSheet = document.createElement('style');
styleSheet.textContent = feedbackStyles;
document.head.appendChild(styleSheet);

window.FeedbackWidget = FeedbackWidget;
