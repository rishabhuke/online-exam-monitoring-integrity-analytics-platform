document
.getElementById("generateBtn")
.addEventListener("click", async function () {

    const subject =
        document.getElementById("subject").value.trim();

    const topic =
        document.getElementById("topic").value.trim();

    const difficulty =
        document.querySelector(
            'input[name="difficulty"]:checked'
        ).value;

    const count =
        parseInt(
            document.getElementById("count").value
        );
        const duration =
parseInt(document.getElementById("duration").value);
const startTime =
document.getElementById("startTime").value;

const endTime =
document.getElementById("endTime").value;

if(startTime===""){

    alert("Select Start Time");

    return;

}

if(endTime===""){

    alert("Select End Time");

    return;

}

if(new Date(endTime) <= new Date(startTime)){

    alert("End Time must be greater than Start Time");

    return;

}

    if(subject===""){

        alert("Enter Subject");

        return;

    }

    if(topic===""){

        alert("Enter Topic");

        return;

    }

    if(isNaN(count)||count<1){

        alert("Invalid Question Count");

        return;

    }

    const quizData={

        subject,

        topic,

        difficulty,

        count,

        duration

    };

    try{

        const response=
        await fetch("/generate_quiz",{

            method:"POST",

            headers:{

                "Content-Type":"application/json"

            },

            body:JSON.stringify(quizData)

        });

        const result=
        await response.json();

        console.log(result);

        if(result.status==="success"){

           const preview =
document.getElementById("quizPreview");

const container =
document.getElementById("questionsContainer");

container.innerHTML = "";

preview.style.display = "block";

result.questions.forEach((q,index)=>{

    container.innerHTML += `

        <div class="question-card">

            <h3>Question ${index+1}</h3>

            <p>${q.question}</p>

            <ul>

                <li>A. ${q.option_a}</li>

                <li>B. ${q.option_b}</li>

                <li>C. ${q.option_c}</li>

                <li>D. ${q.option_d}</li>

            </ul>

            <p class="correct">
                Correct Answer :
                ${q.correct_option}
            </p>

        </div>

    `;

});

window.generatedQuiz = result.questions;

        }

        else{

            alert(result.message);

        }

    }

    catch(error){

        console.error(error);

        alert("Server Error");

    }

});
document
.getElementById("saveQuizBtn")
.addEventListener("click", async function(){

    if(!window.generatedQuiz){

        alert("Generate Quiz First");

        return;

    }

    const data={

    subject:
    document.getElementById("subject").value,

    topic:
    document.getElementById("topic").value,

    difficulty:
    document.querySelector(
        'input[name="difficulty"]:checked'
    ).value,

    duration:
    parseInt(
        document.getElementById("duration").value
    ),

    start_time:
    document.getElementById("startTime").value,

    end_time:
    document.getElementById("endTime").value,

    questions:
    window.generatedQuiz

};

    const response=
    await fetch("/save_quiz",{

        method:"POST",

        headers:{

            "Content-Type":"application/json"

        },

        body:JSON.stringify(data)

    });

    const result=
    await response.json();

    alert(result.message);

});