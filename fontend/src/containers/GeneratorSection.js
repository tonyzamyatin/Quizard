import React, {useState} from "react";
import ConfigContainer from "../components/generation_section/1_configuration/ConfigContainer";
import UploadContainer from "../components/generation_section/2_text_upload/UploadContainer";
import GenerationProgressContainer from "../components/generation_section/3_flashcard_generation/GenerationProgressContainer";
import GenerationSteps from "../components/global/GenerationSteps";

function GeneratorSection() {

    // TODO: Send data from configuration and text input to backend and initiates generation when "Generate Button" is used.

    const [currentStep, setCurrentStep] = useState(GenerationSteps.CONFIGURATION);
    const [text, setText] = useState('');
    const [lang, setLang] = useState('');
    const [mode, setMode] = useState('');
    const [exportFormat, setExportFormat] = useState('')

    // TODO: Get batch numbers from backend
    // Batches of flashcard generation used to calculate progress and display progress bar
    const  [totalBatches, setTotalBatches] = useState(100)
    const [currentBatch, setCurrentBatch] = useState(60);

    // Generated flashcards
    const [flashcards, setFlashcards] = useState([]);


    // TODO: Implement generateFlashcards() and updateProgress() using tasks (and the correct urls xD)
    function updateProgress() {
        fetch('/progress')
            .then(response => response.json())
            .then(data => {
                // Update the progress bar with data.processed_batches
                console.log('Progress:', data.processed_batches);
                if (data.processed_batches < totalBatches) {
                    // Continue polling if the work is not yet done
                    updateProgress();
                }
            })
            .catch(error => console.error('Error:', error));
    }


    // Method to generate flashcards with specified mode and text
    const generateFlashcards = async() => {
        const response = await fetch('http://localhost:5000/api/v1/flashcard/generate',{
            method: 'POST',
            body: JSON.stringify({
                'lang': lang,
                'mode': mode,
                'export_format': exportFormat,
                'inputText': text,
            })
        });
        updateProgress()
        setFlashcards(await response.json());
    }

    // TODO: Add const to make API call to backend:
    // "Generate" -> sends the data from the configuration and the text to the backend and initiates generation, as well
    // as the updates of ProgressBar
    // "Go Back" from GenerationProcessContainer -> stops the generation process, saves the generated flashcard internally.
    // If the user doesn't change the text or config the generate button should say "Continue generating". If the something is changed
    // (i.e. the data is not the same) flashcards are discarded, and the button says "Generate". Reverting changes so that the
    // data is the same as used for the previous flashcard generation counts as "unchanged".
    const renderContent = () => {
        switch (currentStep) {
            case GenerationSteps.CONFIGURATION:
                return <ConfigContainer setGenerationStep={setCurrentStep} lang={lang} setLang={setLang} mode={mode} setMode={setMode} exportFormat={exportFormat} setExportFormat={setExportFormat}/>;
            case GenerationSteps.TEXT_UPLOAD:
                return <UploadContainer setGenerationStep={setCurrentStep} text={text} setText={setText} generateFlashcards={generateFlashcards}/>;
            case GenerationSteps.GENERATION:
                return <GenerationProgressContainer setGenerationStep={setCurrentStep} totalBatches={totalBatches} currentBatch={currentBatch} flashcards={flashcards}/>
        }
    }

    return (
        <div className="generator-section">
            <div className="description">
                <h1>Quizard Flashcard Generator</h1>
                {/*TODO: Add our own paragraph*/}
                <p>Our Flashcard Generator automatically transforms your notes or textbooks into flashcards using
                    the
                    power of artificial intelligence. Simply upload your materials and let our AI create your
                    flashcards
                    in seconds.</p>
            </div>
            {renderContent()}
        </div>
    );
}

export default GeneratorSection;