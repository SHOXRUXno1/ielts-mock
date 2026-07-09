"""
One-shot script to set passage texts for Cambridge IELTS 1 Test 1 Reading sections.
Run from backend/: venv\Scripts\python.exe scripts/update_reading_passages.py
"""
import asyncio
import sys
import uuid

sys.path.insert(0, ".")

# ── Passage 1 ────────────────────────────────────────────────────────────────
PASSAGE_1_ID = uuid.UUID("534d2ac9-b5a3-5f49-a2a3-71f5f8257819")
PASSAGE_1_TEXT = """A spark, a flint: How fire leapt to life

The control of fire was the first and perhaps greatest of humanity's steps towards a life-enhancing technology.

To early man, fire was a divine gift randomly delivered in the form of lightning, forest fire or burning lava. Unable to make flame for themselves, the earliest peoples probably stored fire by keeping slow burning logs alight or by carrying charcoal in pots.

How and where man learnt how to produce flame at will is unknown. It was probably a secondary invention, accidentally made during tool-making operations with wood or stone. Studies of primitive societies suggest that the earliest method of making fire was through friction. European peasants would insert a wooden drill in a round hole and rotate it briskly between their palms. This process could be speeded up by wrapping a cord around the drill and pulling on each end.

The Ancient Greeks used lenses or concave mirrors to concentrate the sun's rays and burning glasses were also used by Mexican Aztecs and the Chinese.

Percussion methods of fire-lighting date back to Paleolithic times, when some Stone Age tool-makers discovered that chipping flints produced sparks. The technique became more efficient after the discovery of iron, about 5000 years ago. In Arctic North America, the Eskimos produced a slow-burning spark by striking quartz against iron pyrites, a compound that contains sulphur. The Chinese lit their fires by striking porcelain with bamboo. In Europe, the combination of steel, flint and tinder remained the main method of fire-lighting until the mid 19th century.

Fire-lighting was revolutionised by the discovery of phosphorus, isolated in 1669 by a German alchemist trying to transmute silver into gold. Impressed by the element's combustibility, several 17th century chemists used it to manufacture fire-lighting devices, but the results were dangerously inflammable. With phosphorus costing the equivalent of several hundred pounds per ounce, the first matches were expensive.

The quest for a practical match really began after 1781 when a group of French chemists came up with the Phosphoric Candle or Ethereal Match, a sealed glass tube containing a twist of paper tipped with phosphorus. When the tube was broken, air rushed in, causing the phosphorus to self-combust. An even more hazardous device, popular in America, was the Instantaneous Light Box - a bottle filled with sulphuric acid into which splints treated with chemicals were dipped.

The first matches resembling those used today were made in 1827 by John Walker, an English pharmacist who borrowed the formula from a military rocket-maker called Congreve. Costing a shilling a box, Congreves were splints coated with sulphur and tipped with potassium chlorate. To light them, the user drew them quickly through folded glass paper.

Walker never patented his invention, and three years later it was copied by a Samuel Jones, who marketed his product as Lucifers. About the same time, a French chemistry student called Charles Sauria produced the first "strike-anywhere" match by substituting white phosphorus for the potassium chlorate in the Walker formula. However, since white phosphorus is a deadly poison, from 1845 match-makers exposed to its fumes succumbed to necrosis, a disease that eats away jaw-bones. It wasn't until 1906 that the substance was eventually banned.

That was 62 years after a Swedish chemist called Pasch had discovered non-toxic red or amorphous phosphorus, a development exploited commercially by Pasch's compatriot J E Lundstrom in 1885. Lundstrom's safety matches were safe because the red phosphorus was non-toxic; it was painted on to the striking surface instead of the match tip, which contained potassium chlorate with a relatively high ignition temperature of 182 degrees centigrade.

America lagged behind Europe in match technology and safety standards. It wasn't until 1900 that the Diamond Match Company bought a French patent for safety matches - but the formula did not work properly in the different climatic conditions prevailing in America and it was another 11 years before scientists finally adapted the French patent for the US.

The Americans, however, can claim several "firsts" in match technology and marketing. In 1892 the Diamond Match Company pioneered book matches. The innovation didn't catch on until after 1896, when a brewery had the novel idea of advertising its product in match books. Today book matches are the most widely used type in the US, with 90 percent handed out free by hotels, restaurants and others.

Other American innovations include an anti-after-glow solution to prevent the match from smouldering after it has been blown out; and the waterproof match, which lights after eight hours in water."""


# ── Passage 3 ────────────────────────────────────────────────────────────────
PASSAGE_3_ID = uuid.UUID("542bc902-cfb6-5c94-940b-7f9506c3992b")
PASSAGE_3_TEXT = """Architecture - Reaching for the Sky

Architecture is the art and science of designing buildings and structures. A building reflects the scientific and technological achievements of the age as well as the ideas and aspirations of the designer and client. The appearance of individual buildings, however, is often controversial.

The use of an architectural style cannot be said to start or finish on a specific date. Neither is it possible to say exactly what characterises a particular movement. But the origins of what is now generally known as modern architecture can be traced back to the social and technological changes of the 18th and 19th centuries.

Instead of using timber, stone and traditional building techniques, architects began to explore ways of creating buildings by using the latest technology and materials such as steel, glass and concrete strengthened steel bars, known as reinforced concrete. Technological advances also helped bring about the decline of rural industries and an increase in urban populations as people moved to the towns to work in the new factories. Such rapid and uncontrolled growth helped to turn parts of cities into slums.

By the 1920s architects throughout Europe were reacting against the conditions created by industrialisation. A new style of architecture emerged to reflect more idealistic notions for the future. It was made possible by new materials and construction techniques and was known as Modernism.

By the 1930s many buildings emerging from this movement were designed in the International Style. This was largely characterised by the bold use of new materials and simple, geometric forms, often with white walls supported by stilt-like pillars. These were stripped of unnecessary decoration that would detract from their primary purpose - to be used or lived in.

Walter Gropius, Charles Jeanneret (better known as Le Corbusier) and Ludwig Mies van der Rohe were among the most influential of the many architects who contributed to the development of Modernism in the first half of the century. But the economic depression of the 1930s and the second world war (1939-45) prevented their ideas from being widely realised until the economic conditions improved and war-torn cities had to be rebuilt. By the 1950s, the International Style had developed into a universal approach to building, which standardised the appearance of new buildings in cities across the world.

Unfortunately, this Modernist interest in geometric simplicity and function became exploited for profit. The rediscovery of quick-and-easy-to-handle reinforced concrete and an improved ability to prefabricate building sections meant that builders could meet the budgets of commissioning authorities and handle a renewed demand for development quickly and cheaply. But this led to many badly designed buildings, which discredited the original aims of Modernism.

Influenced by Le Corbusier's ideas on town planning, every large British city built multi-storey housing estates in the 1960s. Mass-produced, low-cost high-rises seemed to offer a solution to the problem of housing a growing inner-city population. But far from meeting human needs, the new estates often proved to be windswept deserts lacking essential social facilities and services. Many of these buildings were poorly designed and constructed and have since been demolished.

By the 1970s, a new respect for the place of buildings within the existing townscape arose. Preserving historic buildings or keeping only their facades (or fronts) grew common. Architects also began to make more use of building styles and materials that were traditional to the area. The architectural style usually referred to as High Tech was also emerging. It celebrated scientific and engineering achievements by openly parading the sophisticated techniques used in construction. Such buildings are commonly made of metal and glass; examples are Stansted airport and the Lloyd's building in London.

Disillusionment at the failure of many of the poor imitations of Modernist architecture led to interest in various styles and ideas from the past and present. By the 1980s the coexistence of different styles of architecture in the same building became known as Post Modern. Other architects looked back to the classical tradition. The trend in architecture now favours smaller scale building design that reflects a growing public awareness of environmental issues such as energy efficiency. Like the Modernists, people today recognise that a well designed environment improves the quality of life but is not necessarily achieved by adopting one well defined style of architecture.

Twentieth century architecture will mainly be remembered for its tall buildings. They have been made possible by the development of light steel frames and safe passenger lifts. They originated in the US over a century ago to help meet the demand for more economical use of land. As construction techniques improved, the skyscraper became a reality."""


async def main() -> None:
    from app.core.database import engine
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.models.section import Section

    async with AsyncSession(engine) as db:
        # Update Passage 1
        sec1 = await db.get(Section, PASSAGE_1_ID)
        if sec1 is None:
            print(f"Section {PASSAGE_1_ID} not found!")
        else:
            sec1.passage = PASSAGE_1_TEXT
            print(f"Set Passage 1: {len(PASSAGE_1_TEXT)} chars")

        # Update Passage 3
        sec3 = await db.get(Section, PASSAGE_3_ID)
        if sec3 is None:
            print(f"Section {PASSAGE_3_ID} not found!")
        else:
            sec3.passage = PASSAGE_3_TEXT
            print(f"Set Passage 3: {len(PASSAGE_3_TEXT)} chars")

        await db.commit()
        print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
