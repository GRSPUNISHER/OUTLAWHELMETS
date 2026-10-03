[ComponentEditorProps(category: "OUTLAW/Helmets", description: "Hides a helmet part for its wearer while in first person view")]
class OUTLAW_FirstPersonHideComponentClass : ScriptComponentClass
{
}

class OUTLAW_FirstPersonHideComponent : ScriptComponent
{
	protected static const int ALPHA_VISIBLE = 0;
	protected static const int ALPHA_HIDDEN = 255;

	protected ParametricMaterialInstanceComponent m_Material;
	protected bool m_bHidden;

	override void OnPostInit(IEntity owner)
	{
		m_Material = ParametricMaterialInstanceComponent.Cast(owner.FindComponent(ParametricMaterialInstanceComponent));
		if (m_Material)
			m_Material.SetUserAlphaTestParam(ALPHA_VISIBLE);

		if (System.IsConsoleApp())
			return;

		SetEventMask(owner, EntityEvent.FRAME);
	}

	override void EOnFrame(IEntity owner, float timeSlice)
	{
		bool hide = ShouldHide(owner);
		if (hide == m_bHidden)
			return;

		m_bHidden = hide;
		if (m_Material)
		{
			if (hide)
				m_Material.SetUserAlphaTestParam(ALPHA_HIDDEN);
			else
				m_Material.SetUserAlphaTestParam(ALPHA_VISIBLE);

			return;
		}

		if (hide)
			owner.ClearFlags(EntityFlags.VISIBLE, false);
		else
			owner.SetFlags(EntityFlags.VISIBLE, false);
	}

	protected bool ShouldHide(IEntity owner)
	{
		IEntity root = owner.GetRootParent();
		if (!root || root == owner)
			return false;

		if (root != SCR_PlayerController.GetLocalControlledEntity())
			return false;

		ChimeraCharacter character = ChimeraCharacter.Cast(root);
		if (!character)
			return false;

		CharacterControllerComponent controller = character.GetCharacterController();
		if (!controller)
			return false;

		return !controller.IsInThirdPersonView();
	}
}
