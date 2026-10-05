"""Assistant de formation.

Lit un document texte, puis demande à un modèle de langage (LLM) local, lancé avec
Ollama, d'en faire un résumé et un quiz. Le résultat est enregistré dans un fichier.

Utilisation :
    python assistant_formation.py information_aeronautique.txt
"""

import sys
from pathlib import Path

import ollama

MODELE = "llama3.2"        # modèle téléchargé avec : ollama pull llama3.2
NB_POINTS = 5              # nombre de points dans le résumé
NB_QUESTIONS = 3           # nombre de questions dans le quiz
MAX_CARACTERES = 6000      # au-delà, le document est coupé pour tenir dans la mémoire du modèle


def lire_document(chemin):
    """Ouvre le fichier texte et renvoie son contenu."""
    texte = Path(chemin).read_text(encoding="utf-8").strip()
    if len(texte) > MAX_CARACTERES:
        print(f"Document long : seuls les {MAX_CARACTERES} premiers caractères sont utilisés.")
        texte = texte[:MAX_CARACTERES]
    return texte


def demander_au_modele(instruction, texte):
    """Envoie une instruction (prompt) et le document au modèle, puis renvoie sa réponse."""
    reponse = ollama.chat(
        model=MODELE,
        messages=[
            {
                "role": "system",
                "content": "Tu es un formateur. Réponds en français, uniquement à partir du document fourni.",
            },
            {"role": "user", "content": f"{instruction}\n\nDOCUMENT :\n{texte}"},
        ],
        options={"num_ctx": 4096},  # taille de la mémoire de travail du modèle
    )
    return reponse["message"]["content"].strip()


def resumer(texte):
    """Demande au modèle un résumé en quelques points."""
    instruction = f"Résume ce document en exactement {NB_POINTS} points clés, sous forme de liste à puces."
    return demander_au_modele(instruction, texte)


def generer_quiz(texte):
    """Demande au modèle des questions à choix multiples avec leurs réponses."""
    instruction = (
    f"Écris {NB_QUESTIONS} questions à choix multiples sur ce document. "
    "Pour chaque question, propose 3 choix (A, B, C), sans donner la réponse. "
    "Termine par une partie intitulée « Réponses » qui donne la bonne lettre de chaque question.")
    return demander_au_modele(instruction, texte)


def enregistrer(chemin_document, resume, quiz):
    """Écrit la fiche de formation dans un fichier placé à côté du document."""
    document = Path(chemin_document)
    fiche = document.with_name(document.stem + "_fiche.md")
    contenu = f"# Fiche de formation : {document.name}\n\n## Résumé\n\n{resume}\n\n## Quiz\n\n{quiz}\n"
    fiche.write_text(contenu, encoding="utf-8")
    return fiche


def main():
    if len(sys.argv) != 2:
        print("Utilisation : python assistant_formation.py <fichier.txt>")
        return 1

    chemin = sys.argv[1]
    try:
        texte = lire_document(chemin)
    except (OSError, UnicodeDecodeError):
        print(f"Impossible de lire le fichier : {chemin} (vérifiez son nom et qu'il est enregistré en UTF-8)")
        return 1
    if not texte:
        print("Le document est vide.")
        return 1

    try:
        print("1/2 Résumé en cours...")
        resume = resumer(texte)
        print("2/2 Quiz en cours...")
        quiz = generer_quiz(texte)
    except ConnectionError:
        print("Impossible de joindre Ollama. Vérifiez qu'Ollama est installé et lancé.")
        return 1
    except ollama.ResponseError as erreur:
        print(f"Le modèle a renvoyé une erreur : {erreur}")
        print(f"Avez-vous téléchargé le modèle avec « ollama pull {MODELE} » ?")
        return 1

    fiche = enregistrer(chemin, resume, quiz)
    print(f"Fiche enregistrée : {fiche}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
